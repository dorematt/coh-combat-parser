import sys
from PyQt5.QtWidgets import QMessageBox, QSizePolicy, QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QFileDialog, QHBoxLayout, QTreeWidgetItemIterator, QTabWidget
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSlot, QMutex, QMutexLocker, pyqtSignal, QSettings
from combat.CombatParser import Parser, CombatSession, Character, Ability, DamageComponent
from data.Globals import Globals
import random
from ui.Settings import SettingsWindow
from ui.style.Theme import apply_stylesheet, apply_header_style_fix
import os
from pathlib import Path

class ParserThread(QThread):
    sig_process_live_log = pyqtSignal(str)
    sig_process_existing_log = pyqtSignal(str)
    def __init__(self, file_path : str,live: bool):
        super().__init__()
        self.settings = QSettings(Globals.AUTHOR, Globals.APPLICATION_NAME)
        self.file_path = file_path
        self.live = live
        self.parser = Parser(self)
        if self.settings.value("ConsoleVerbosity", 1, int) >= 2: print("Parser Initialized")
        self.sig_process_live_log.connect(lambda: self.parser.process_live_log(self.file_path))
        self.sig_process_existing_log.connect(lambda: self.parser.process_existing_log(self.file_path))

    def run(self):
        if self.live:
            self.sig_process_live_log.emit(self.file_path)
            ("Emitted Signal: Processing Live Log, with file path: ", self.file_path)
        else:
            self.sig_process_existing_log.emit(self.file_path)
            print("Emitted Signal: Process Existing Log")
        

class MainUI(QMainWindow):
    selected_session = None
    monitoring_live = False
    combat_session_data = []
    parser_thread = QThread()
    WorkerThread = None
    sig_stop_monitoring = pyqtSignal()
    sig_run = pyqtSignal(str)
    sig_run_live = pyqtSignal(str)
    combat_mutex = QMutex() # the lock for interacting with combat session data
    # sig_terminate_processing = pyqtSignal()
    settings = QSettings(Globals.AUTHOR, Globals.APPLICATION_NAME)
    last_file_path = settings.value("last_file_path", "", type=str)
    CONSOLE_VERBOSITY = settings.value("ConsoleVerbosity", Globals.DEFAULT_CONSOLE_VERBOSITY, int)


    def __init__(self,):
        super().__init__()

        # Initialization code here
        print("Initializing UI...")

        def define_main_window():
            # Set up the main window
            self.setGeometry(200, 200, 1400, 700)
            self.setWindowTitle("CoH Log Combat Parser - v" + Globals.VERSION)

            # Initialize UI Variables
            self.file_path_var = QLineEdit(self.last_file_path)
            self.overall_dps_var = QLabel("DPS:")

            # File path input label and entry
            self.file_path_label = QLabel("Log File Path:")
            self.browse_button = QPushButton("Browse", clicked=self.browse_file)
            self.settings_button = QPushButton("Settings", clicked=self.open_settings_window)

            # Start/Stop and Process buttons
            self.start_stop_button = QPushButton("Start Log", clicked=self.start_stop_log)
            self.process_button = QPushButton("Process Existing Log", clicked=self.process_existing_log)

            # Run Test button to add test data to the Treeview
            self.run_test_button = QPushButton("Run Test", clicked=self.run_test_log)


        def define_combat_session_tree():
            # Combat Session Tree
            self.combat_session_tree = QTreeWidget()
            self.combat_session_tree.setHeaderLabels(["Session", "Duration", "DPS", "EXP", "Inf"])
            apply_header_style_fix(self.combat_session_tree)
            self.combat_session_tree.setColumnWidth(0, 150)
            self.combat_session_tree.setColumnWidth(1, 75)
            self.combat_session_tree.setColumnWidth(2, 75)
            self.combat_session_tree.setColumnWidth(3, 80)
            self.combat_session_tree.setColumnWidth(4, 80)
            self.combat_session_tree.setSelectionMode(QTreeWidget.SingleSelection)
            self.combat_session_tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.combat_session_tree.setMinimumWidth(250)
            self.combat_session_tree.setMaximumWidth(500)

            self.combat_session_tree.itemSelectionChanged.connect(self.on_session_selection_change)

        def define_ability_tree_tabs():
            # Set up view tabs for the ability tree
            self.view_tabs = QTabWidget()

            # Create two separate ability tree displays for player and enemies
            self.ability_tree_display_player = QTreeWidget()
            self.ability_tree_display_enemies = QTreeWidget()

            # Configure the columns for both trees (assuming they have the same structure)
            for tree_widget in [self.ability_tree_display_player, self.ability_tree_display_enemies]:
                tree_widget.setSortingEnabled(True)
                tree_widget.setHeaderLabels([
                    "Name", "DPS", "Acc %", "Avg Per Hit", "Count",
                    "Max", "Min", "Total", "Hits", "Tries"
                ])
                apply_header_style_fix(tree_widget)

                tree_widget.setColumnWidth(0, 275)
                tree_widget.setColumnWidth(1, 75)
                tree_widget.setColumnWidth(2, 100)
                tree_widget.setColumnWidth(3, 100)
                tree_widget.setColumnWidth(4, 75)
                tree_widget.setColumnWidth(5, 75)
                tree_widget.setColumnWidth(6, 75)
                tree_widget.setColumnWidth(7, 100)
                tree_widget.setColumnWidth(8, 75)
                tree_widget.setColumnWidth(9, 75)
                tree_widget.setMinimumWidth(500)

                # Set the default sort column to DPS
                tree_widget.sortByColumn(1, Qt.DescendingOrder)

            # Add ability trees to the view tabs
            self.view_tabs.addTab(self.ability_tree_display_player, "Player")
            self.view_tabs.addTab(self.ability_tree_display_enemies, "Enemies")

        def setup_layout():
            # Set up the layout
            browse_layout = QHBoxLayout()
            browse_layout.addWidget(self.file_path_label)
            browse_layout.addWidget(self.file_path_var)
            browse_layout.addWidget(self.browse_button)
            browse_layout.addWidget(self.settings_button)

            button_layout = QHBoxLayout()
            button_layout.addWidget(self.start_stop_button)
            button_layout.addWidget(self.process_button)
            #button_layout.addWidget(self.run_test_button)

            combat_tree_layout = QHBoxLayout()
            # combat_tree_layout.columnCount = 5
            combat_tree_layout.addWidget(self.combat_session_tree)
            combat_tree_layout.addWidget(self.view_tabs)  # Add the view tabs to the layout

            main_layout = QVBoxLayout()
            main_layout.addLayout(browse_layout)
            main_layout.addLayout(button_layout)
            main_layout.addLayout(combat_tree_layout)

            central_widget = QWidget()
            central_widget.setLayout(main_layout)
            self.setCentralWidget(central_widget)

        if self.settings.value("AutoUpdateLogFile", Globals.DEFAULT_AUTO_UPDATE_LOG_FILE, bool):
            self.last_file_path = self.check_for_latest_file(self.last_file_path)

        define_main_window()
        define_combat_session_tree()
        define_ability_tree_tabs()  # Initialize the view tabs
        setup_layout()
        apply_stylesheet(self)

        print("Done.")


    def start_worker_thread(self, file_path: str, live: bool):
        
        if self.CONSOLE_VERBOSITY >= 2: print("Starting Worker Thread...")
        self.WorkerThread = ParserThread(file_path, live)
        self.WorkerThread.parser.sig_finished.connect(self.on_worker_finished)
        self.WorkerThread.parser.sig_periodic_update.connect(lambda: self.on_sig_periodic_update(self.WorkerThread.parser.combat_session_data))
        self.sig_stop_monitoring.connect(self.WorkerThread.parser.on_sig_stop_monitoring)
        self.WorkerThread.start()
        self.settings.setValue("last_file_path", file_path)
        if self.CONSOLE_VERBOSITY >= 2: print("Worker Thread Started: ", self.WorkerThread.isRunning())

   # @pyqtSlot()
    def start_stop_log(self):

        if self.file_path_var.text() == "": self.browse_file()
        file_path = self.file_path_var.text()
        if self.check_file_path_valid(file_path) == False: return

        if  self.monitoring_live == False:
            self.start_stop_button.setText("Stop Log")
            self.lock_ui()
            self.start_stop_button.setEnabled(True)
            self.monitoring_live = True
            self.start_worker_thread(file_path, True)
            self.ability_tree_display_player.clear()
            self.ability_tree_display_enemies.clear()
            self.combat_session_tree.clear()

        else:
            self.unlock_ui()
            self.monitoring_live = False
            self.start_stop_button.setText("Start Log")
            self.sig_stop_monitoring.emit()

   # @pyqtSlot()
    def process_existing_log(self):
        
        if self.file_path_var.text() == "": self.browse_file()
        file_path = self.file_path_var.text()
        if self.check_file_path_valid(file_path) == False: return


        if self.process_button.text() == "Process Existing Log":
            
            #Lock UI
            self.process_button.setText("Stop Processing")
            self.lock_ui()
            self.start_worker_thread(file_path, False)
            self.ability_tree_display_player.clear()
            self.ability_tree_display_enemies.clear()
            self.combat_session_tree.clear()
            self.process_button.setEnabled(True)

        else:
            print("Terminating Parser Processing...")
            self.process_button.setEnabled(False)
            self.sig_stop_monitoring.emit()
            self.process_button.setText("Process Existing Log")


    def on_worker_finished(self, data):
        with QMutexLocker(self.combat_mutex):
            self.combat_session_data = data
            self.sig_run.disconnect
            self.WorkerThread.parser.sig_finished.disconnect
            self.WorkerThread.parser.sig_periodic_update.disconnect
            self.WorkerThread.quit()
            if self.CONSOLE_VERBOSITY >= 2: print("Worker Thread Quit")
            self.unlock_ui()
            self.process_button.setText("Process Existing Log")
            if self.combat_session_data != []:
                self.selected_session = self.combat_session_data[-1]
                self.repopulate_sessions(self.combat_session_data)
                self.repopulate(self.selected_session)

    @pyqtSlot()
    def on_sig_periodic_update(self, data):
        '''Signal to update the UI with the latest data from the parser thread'''
        with QMutexLocker(self.combat_mutex):
            
            self.combat_session_data = data
            if data == [] or self.combat_session_data is None:
                self.selected_session = []
            #check if user has selected a session, if they have, keep it selected
            else:
                self.selected_session = self.combat_session_data[-1]

            self.repopulate_sessions(self.combat_session_data)
            self.repopulate(self.selected_session)
            self
        
    def on_session_selection_change(self):
        '''Handles the event when a combat session is selected in the treeWidget'''
        if self.combat_session_tree.selectedItems():
            with QMutexLocker(self.combat_mutex):
                selected_index = self.combat_session_tree.selectedIndexes()[0].row()
                self.selected_session = self.combat_session_data[selected_index]
                self.repopulate(self.selected_session)
    


    def update_or_create_item(tree_widget, parent_item, text_list, unique_key):
        """Update an existing item or create a new one if it doesn't exist."""
        items = tree_widget.findItems(unique_key, Qt.MatchExactly | Qt.MatchRecursive, 0)
        if items:
            item = items[0]
        else:
            item = QTreeWidgetItem(parent_item, text_list)
            item.setText(0, unique_key)
        for i, text in enumerate(text_list):
            item.setText(i, text)
        return item

    def repopulate_sessions(self, combat_session_list: list):
        '''Populates the treeWidget with data from the provided list of combat sessions. This should only be called while under a mutex lock'''
        assert not(self.combat_mutex.tryLock()), "UI Repopulation mutex not acquired"


        # Clear the treeWidget and rebuild
        self.combat_session_tree.clear()
        if combat_session_list == []: return
        for session, combat_session in enumerate(combat_session_list, start=1):
            session_name = combat_session_list[session-1].get_name()
            session_item = QTreeWidgetItem(self.combat_session_tree, [session_name])
            session_item.setText(1, str(combat_session.duration) + "s")
            session_item.setText(2, str(combat_session.get_dps()))
            session_item.setText(3, "{:,}".format(combat_session.get_exp()))
            session_item.setText(4, "{:,}".format(combat_session.get_inf()))


    def repopulate(self, session):
        '''This is the main function to clear and populate the ability tree with data from the provided combat session. This should only be called while under a mutex lock
        TODO: Make this more efficient by only updating the changed data, rather than clearing and repopulating the entire treeWidget'''

        def set_styling(item, font_size=10, is_bold=False, background_color=None):
            for i in range(10):
                item.setFont(i, QFont("Fira Sans Medium", font_size, QFont.Bold if is_bold else QFont.Normal))
                if background_color:
                    item.setBackground(i, background_color)

        def save_ability_tree_state(tree_widget):
            item_state = {}
            iterator = QTreeWidgetItemIterator(tree_widget)
            while iterator.value():
                item = iterator.value()
                id = item.data(0,Qt.UserRole)
                item_state[id] = item.isExpanded()
                iterator += 1
            return item_state

        def restore_ability_tree_state(tree_widget, expanded_items):
            iterator = QTreeWidgetItemIterator(tree_widget)
            while iterator.value():
                item = iterator.value()
                id = item.data(0,Qt.UserRole)
                if id in expanded_items:
                    item.setExpanded(expanded_items[id])
                iterator += 1
                
        def create_character_item(tree_widget, character_name, duration):
            character_item = QTreeWidgetItem(tree_widget, [character_name])
            set_styling(character_item, font_size=11, is_bold=True, background_color=QColor(25, 25, 25))
            character_item.setData(0, Qt.UserRole, character_name)
            character_item.setData(1, Qt.DisplayRole, character.get_dps(duration))
            character_item.setData(2, Qt.DisplayRole, "{:,}%".format(character.get_accuracy()))
            character_item.setData(3, Qt.DisplayRole, character.get_average_damage())
            character_item.setData(4, Qt.DisplayRole, character.get_count())
            character_item.setData(7, Qt.DisplayRole, int(character.get_total_damage()))
            character_item.setData(8, Qt.DisplayRole, character.get_hits())
            character_item.setData(9, Qt.DisplayRole, character.get_tries())

            character_item.setTextAlignment(2, Qt.AlignCenter)
            character_item.setTextAlignment(3, Qt.AlignCenter)
            character_item.setTextAlignment(4, Qt.AlignCenter)
            character_item.setTextAlignment(5, Qt.AlignCenter)
            character_item.setTextAlignment(6, Qt.AlignCenter)
            character_item.setTextAlignment(7, Qt.AlignCenter)
            character_item.setTextAlignment(8, Qt.AlignCenter)

            return character_item

        def create_ability_item(parent_item:str, ability_name, duration):
            ability_item = QTreeWidgetItem(parent_item, [ability_name])
            ability_item.setData(0, Qt.UserRole, str(parent_item.data(0,Qt.UserRole)+ability_name))
            ability_item.setData(1, Qt.DisplayRole, ability.get_dps(duration))
            # ability_item.setData(2, Qt.DisplayRole, "{:,}%".format(ability.get_accuracy()))
            ability_item.setData(2, Qt.DisplayRole, ability.get_accuracy())
            ability_item.setData(3, Qt.DisplayRole, ability.get_average_damage())
            ability_item.setData(4, Qt.DisplayRole, ability.get_count())
            ability_item.setData(5, Qt.DisplayRole, ability.get_max_damage())
            ability_item.setData(6, Qt.DisplayRole, ability.get_min_damage())
            ability_item.setData(7, Qt.DisplayRole, int(ability.get_total_damage()))
            ability_item.setData(8, Qt.DisplayRole, ability.get_hits())
            ability_item.setData(9, Qt.DisplayRole, ability.get_tries())

            ability_item.setTextAlignment(2, Qt.AlignCenter)
            ability_item.setTextAlignment(3, Qt.AlignCenter)
            ability_item.setTextAlignment(4, Qt.AlignCenter)
            ability_item.setTextAlignment(5, Qt.AlignCenter)
            ability_item.setTextAlignment(6, Qt.AlignCenter)
            ability_item.setTextAlignment(7, Qt.AlignCenter)
            ability_item.setTextAlignment(8, Qt.AlignCenter)

            return ability_item

        def create_damage_item(parent_item, damage_name, duration):
            damage_item = QTreeWidgetItem(parent_item, [damage_name.name])
            damage_item.setData(0, Qt.UserRole, str(parent_item.data(0,Qt.UserRole)+damage_name.name))
            damage_item.setData(1, Qt.DisplayRole, damage_name.get_dps(duration))
            damage_item.setData(3, Qt.DisplayRole, damage_name.get_average_damage())
            damage_item.setData(4, Qt.DisplayRole, damage_name.get_count())
            damage_item.setData(5, Qt.DisplayRole, damage_name.get_highest_damage())
            damage_item.setData(6, Qt.DisplayRole, damage_name.get_lowest_damage())
            damage_item.setData(7, Qt.DisplayRole, int(damage_name.get_damage()))
            

            damage_item.setTextAlignment(2, Qt.AlignCenter)
            damage_item.setTextAlignment(3, Qt.AlignCenter)
            damage_item.setTextAlignment(4, Qt.AlignCenter)
            damage_item.setTextAlignment(5, Qt.AlignCenter)
            damage_item.setTextAlignment(6, Qt.AlignCenter)
            damage_item.setTextAlignment(7, Qt.AlignCenter)

            return damage_item

        # asset mutex lock is in place
        assert not(self.combat_mutex.tryLock()), "UI Repopulation mutex not acquired"
        for tree_widget in [self.ability_tree_display_player, self.ability_tree_display_enemies]:

            tree_state = save_ability_tree_state(tree_widget)
            current_column = tree_widget.header().sortIndicatorSection()
            current_order = tree_widget.header().sortIndicatorOrder()
            tree_widget.clear()

            # Repopulate the treeWidget
            if session is None or session == []:
                return

            if tree_widget == self.ability_tree_display_player:
                char_list = session.chars
            else:
                char_list = session.targets

            duration = session.duration
            for character_name, character in char_list.items():
                character_item = create_character_item(tree_widget, character_name, duration)

                for ability_name, ability in character.abilities.items():
                    ability_item = create_ability_item(character_item, ability_name, duration)

                    for damage_name in ability.damage:
                        create_damage_item(ability_item, damage_name, duration)

            # Set initial tree expansion (player view only
            if tree_widget == self.ability_tree_display_player: tree_widget.expandToDepth(0)

            # Restore user tree state
            restore_ability_tree_state(tree_widget, tree_state)
            
            # Restore user sorting
            tree_widget.sortByColumn(current_column, current_order)
            


    def browse_file(self):
        self.lock_ui()
        file_path, _ = QFileDialog.getOpenFileName(directory=self.last_file_path, filter="Text Files (*.txt)")
        if file_path != "":
            self.file_path_var.setText(file_path)
            self.settings.setValue("last_file_path", file_path)
        self.unlock_ui()

    def check_for_latest_file(self, file_path: str) -> str:
        if file_path == "":
            return ""
        # Convert the input path to a Path object
        original_file = Path(file_path)

        # Get the directory containing the file
        directory = original_file.parent

        # Get the creation time of the original file
        original_creation_time = original_file.stat().st_ctime

        # Initialize a variable to keep track of the most recent file
        most_recent_file = original_file
        most_recent_time = original_creation_time

        # Iterate over all .txt files in the directory
        for file in directory.glob('*.txt'):
            # Check the creation time of the current file
            creation_time = file.stat().st_ctime

            # Update the most recent file if this one is newer
            if creation_time > most_recent_time:
                most_recent_file = file
                most_recent_time = creation_time

        # Return the path of the most recent file
        return str(most_recent_file)

    def open_settings_window(self):
        self.settings_window = SettingsWindow()
        self.settings_window.exec_()

    def error(self, message, title = "Error"):
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle(title)
        error_box.setText(message)
        error_box.exec_()
    def exit(self):
        # Stop the UI
        self.destroy()
    def lock_ui(self):
        self.start_stop_button.setEnabled(False)
        self.process_button.setEnabled(False)
        self.file_path_var.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.run_test_button.setEnabled(False)
        self.settings_button.setEnabled(False)
    def unlock_ui(self):
        self.start_stop_button.setEnabled(True)
        self.process_button.setEnabled(True)
        self.file_path_var.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.run_test_button.setEnabled(True)
        self.settings_button.setEnabled(True)
    def check_file_path_valid(self, file_path: str) -> bool:
        file_path = self.file_path_var.text()
        if file_path == "":
            self.error("No File Path Entered")
            return False
        if not os.path.isfile(file_path):
            self.error("Invalid File Path: " + file_path)
            return False
        return True

    def run_test_log(self):
        # Create a list of test data
        test_sessions = []
        self.ability_tree_display_player.clear()
        self.ability_tree_display_enemies.clear()
        self.combat_session_tree.clear()

        def pick_random_type():
            damage_types = ["Smashing", "Lethal", "Fire", "Cold", "Energy", "Negative", "Toxic", "Psionic"]
            return random.choice(damage_types)
        
        def pick_random_name():
            names = ["Emet", "Positron", "Manticore", "Mynx", "Maelstrom", "Statesman", "Extracted Essence", "Fire Imp"]
            return random.choice(names)
        
        def pick_random_ability():
            abilities = ["Punch", "Kick", "Fire Blast", "Ice Blast", "Energy Blast", "Dark Blast", "Toxic Blast", "Psionic Blast", "Soul Drain"]
            return random.choice(abilities)
        
    # Create a function to set up test data
        def setup_test_data():
            '''Creates a full set of randomised data to '''
            for i in range(0, 4):
                test_sessions.append(CombatSession("Combat Session " + str(i)))
                test_sessions[i].duration = random.randint(60, 180)
                test_sessions[i].add_exp(random.randint(1000, 9999999))
                test_sessions[i].add_inf(random.randint(1000, 9999999))

                for j in range(0, 3): #Combat Sessions
                    character = Character(pick_random_name())
                    test_sessions[i].add_character(character)
                    #character = test_sessions[i].chars[character.name]

                    for k in range(0, random.randint(3, 6)):
                        ability = Ability(pick_random_ability(), True)
                        test_sessions[i].chars[character.name].add_ability(ability.name, ability)
                        # ability = test_sessions[i].chars[character.name].abilities[ability.name]

                        for l in range(0, random.choices([1,2], weights=[0.8, 0.2])[0]):
                            damage = DamageComponent(pick_random_type(), random.randint(0, 100))
                            test_sessions[i].chars[character.name].abilities[ability.name].add_damage(damage, random.randint(0, 100))

                for ii in range(0, random.randint(50, 100)): #Add some hits and damage to the abilities inside the combat session
                    character = random.choice(list(test_sessions[i].chars.values()))
                    ability = random.choice(list(character.abilities.values()))
                    hit = random.choices([True, False], weights=[0.9, 0.1])[0]
                    ability.ability_used()
                    ability.ability_hit(hit)
                    if hit:
                        damage = random.choice(list(ability.damage))
                        damage.add_damage(damage,random.randint(0, 100))
            print("Test Data Created")


        # Call the function to set up test data
        setup_test_data()
        self.combat_session_tree.clear()
        self.ability_tree_display_player.clear()
        self.ability_tree_display_enemies.clear()
        self.combat_session_tree.conn
        with QMutexLocker(self.combat_mutex):
            self.combat_session_data = test_sessions
            # Populate the tree with test data
            # self.repopulate_sessions(self.combat_session_data)


if __name__ == "__main__":
    # Create the UI
    app = QApplication(sys.argv)
    ui = MainUI(parser=Parser())
    ui.show()
    sys.exit(app.exec_())