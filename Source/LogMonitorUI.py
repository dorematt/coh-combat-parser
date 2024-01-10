import sys
from PyQt5.QtWidgets import QMessageBox, QSizePolicy, QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QGridLayout, QWidget, QFileDialog, QHBoxLayout
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSlot, QMutex, QMutexLocker, pyqtSignal, QSettings
from CombatParser import Parser, CombatSession, Character, Ability, DamageComponent
from CoH_Parser import Globals
import random
import os.path

class ParserThread(QThread):
    def __init__(self, file_path: str, live: bool):
        super().__init__()
        self.file_path = file_path
        self.live = live
        self.parser = Parser()

    def run(self):
        if self.live:
            self.parser.process_live_log(self.file_path)
        else:
            self.parser.process_existing_log(self.file_path)
        

class LogMonitorUI(QMainWindow):
    selected_session = None
    parser = None
    monitoring_live = False
    combat_session_data = []
    parser_thread = QThread()
    WorkerThread = None
    sig_stop_monitoring = pyqtSignal()
    sig_run = pyqtSignal(str)
    sig_run_live = pyqtSignal(str)
    # sig_terminate_processing = pyqtSignal()
    settings = QSettings("dorematt", "coh-combat-parser")
    last_file_path = settings.value("last_file_path", "", type=str)


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

            # Start/Stop and Process buttons
            self.start_stop_button = QPushButton("Start Log", clicked=self.start_stop_log)
            self.process_button = QPushButton("Process Existing Log", clicked=self.process_existing_log)

            # Run Test button to add test data to the Treeview
            self.run_test_button = QPushButton("Run Test", clicked=self.run_test_log)
        def define_ability_tree():
            # Main Ability Tree
            self.ability_tree_display = QTreeWidget()
            self.ability_tree_display.setSortingEnabled(True)

            self.ability_tree_display.setHeaderLabels(["Name", "DPS", "Acc %", "Avg Per Hit", "Count", "Max", "Min", "Total"])
            self.ability_tree_display.setColumnWidth(0, 250)
            self.ability_tree_display.setColumnWidth(1, 75)
            self.ability_tree_display.setColumnWidth(2, 75)
            self.ability_tree_display.setColumnWidth(3, 100)
            self.ability_tree_display.setColumnWidth(4, 75)
            self.ability_tree_display.setColumnWidth(5, 75)
            self.ability_tree_display.setColumnWidth(6, 75)
            self.ability_tree_display.setColumnWidth(7, 75)
            self.ability_tree_display.setMinimumWidth(500)

            # Set the default sort column to DPS
            self.ability_tree_display.sortByColumn(1, Qt.DescendingOrder)
        def define_combat_session_tree():
            # Combat Session Tree
            self.combat_session_tree = QTreeWidget()
            self.combat_session_tree.setHeaderLabels(["Session", "Duration","DPS", "EXP", "Inf"])
            self.combat_session_tree.setColumnWidth(0, 100)
            self.combat_session_tree.setColumnWidth(1, 75)
            self.combat_session_tree.setColumnWidth(2, 75)
            self.combat_session_tree.setColumnWidth(3, 80)
            self.combat_session_tree.setColumnWidth(4, 80)
            self.combat_session_tree.setSelectionMode(QTreeWidget.SingleSelection)
            self.combat_session_tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.combat_session_tree.setMinimumWidth(250)
            self.combat_session_tree.setMaximumWidth(420)

            self.combat_session_tree.itemSelectionChanged.connect(self.on_session_selection_change)
        def setup_layout():
    
            # Set up the layout
            browse_layout = QHBoxLayout()
            browse_layout.addWidget(self.file_path_label)
            browse_layout.addWidget(self.file_path_var)
            browse_layout.addWidget(self.browse_button)

            button_layout = QHBoxLayout()
            button_layout.addWidget(self.start_stop_button)
            button_layout.addWidget(self.process_button)
            button_layout.addWidget(self.run_test_button)

            combat_tree_layout = QGridLayout()
            combat_tree_layout.columnCount = 5
            combat_tree_layout.addWidget(self.combat_session_tree, 0, 0)
            combat_tree_layout.addWidget(self.ability_tree_display, 0, 2)

            main_layout = QVBoxLayout()
            main_layout.addLayout(browse_layout)
            main_layout.addLayout(button_layout)
            main_layout.addLayout(combat_tree_layout)

            central_widget = QWidget()
            central_widget.setLayout(main_layout)
            self.setCentralWidget(central_widget)
        
        define_main_window()
        define_ability_tree()
        define_combat_session_tree()
        setup_layout()
        print("Done.")

    def browse_file(self):
        self.lock_ui()
        file_path, _ = QFileDialog.getOpenFileName(directory=self.last_file_path, filter="Text Files (*.txt)")
        self.file_path_var.setText(file_path)
        self.settings.setValue("last_file_path", file_path)
        self.unlock_ui()

    def start_parse_thread(self):
        '''To be replaced by start_worker_thread once working...'''
        self.parser.sig_finished.connect(self.on_parser_finished)
        self.parser.sig_periodic_update.connect(self.on_sig_periodic_update)
        self.parser.moveToThread(self.parser_thread)
        self.parser_thread.start()
        print("Parser Thread Started: ", self.parser_thread.isRunning())

    def start_worker_thread(self, file_path: str, live: bool):
        
        print("Starting Worker Thread...")
        self.WorkerThread = ParserThread(file_path, live)
        self.WorkerThread.parser.sig_finished.connect(self.on_worker_finished)
        self.WorkerThread.parser.sig_periodic_update.connect(lambda: self.on_sig_periodic_update(self.WorkerThread.parser.combat_session_data))
        self.sig_stop_monitoring.connect(self.WorkerThread.parser.on_sig_stop_monitoring)
        self.WorkerThread.start()
        print("Worker Thread Started: ", self.WorkerThread.isRunning())

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
            # self.parser_thread.started.connect(lambda: self.parser.process_live_log(file_path))
            #self.start_parse_thread()
            self.ability_tree_display.clear()
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
            self.process_button.setText("Processing...")
            self.lock_ui()
            # self.process_button.setEnabled(True)
            # self.parser_thread.started.connect(lambda: self.parser.process_existing_log(file_path))
            #self.start_parse_thread()
            self.start_worker_thread(file_path, False)
            self.ability_tree_display.clear()
            self.combat_session_tree.clear()
            #self.WorkerThread.run_existing(file_path)
            #self.sig_run.emit()
            

        elif self.process_button.text == ("Stop Processing"):
            print("Terminating Parser Processing...")
            # self.parser_thread.quit()
            # self.WorkerThread.terminate()
            self.sig_stop_monitoring.emit()
            self.unlock_ui()
            self.process_button.setText("Process Existing Log")

   # @pyqtSlot()
    def on_parser_finished(self):
        self.parser_thread.quit()
        print("Parser Thread Quit")
        self.unlock_ui()
        self.process_button.setText("Process Existing Log")
        with QMutexLocker(self.parser.mutex):
            self.repopulate_sessions(self.parser.combat_session_data)
            self.selected_session = self.parser.combat_session_data[-1]
            self.repopulate(self.selected_session)

    def on_worker_finished(self, data):
        self.combat_session_data = data
        self.sig_run.disconnect
        self.WorkerThread.parser.sig_finished.disconnect
        self.WorkerThread.parser.sig_periodic_update.disconnect
        self.WorkerThread.quit()
        print("Worker Thread Quit")
        self.unlock_ui()
        self.process_button.setText("Process Existing Log")
        if self.combat_session_data != []:
            self.repopulate_sessions(self.combat_session_data)
            self.selected_session = self.combat_session_data[-1]
            self.repopulate(self.selected_session)

    @pyqtSlot()
    def on_sig_periodic_update(self, data):
        self.combat_session_data = data
        self.repopulate_sessions(self.combat_session_data)

        self.selected_session = self.combat_session_data[-1]
        self.repopulate(self.selected_session)
        
    def on_session_selection_change(self):
        '''Handles the event when a combat session is selected in the treeWidget'''
        if self.combat_session_tree.selectedItems():
            selected_index= self.combat_session_tree.selectedIndexes()[0].row()
            self.selected_session = self.combat_session_data[selected_index]
            self.repopulate(self.selected_session)

    def repopulate_sessions(self, combat_session_list: list):
        '''Populates the treeWidget with data from the provided list of combat sessions'''
        # Clear the treeWidget
        self.combat_session_tree.clear()
        for session, combat_session in enumerate(combat_session_list, start=1):
            session_item = QTreeWidgetItem(self.combat_session_tree, [str(session)])
            session_item.setText(1, str(combat_session.duration) + "s")
            session_item.setText(2, str(combat_session.get_dps()))
            session_item.setText(3, "{:,}".format(combat_session.get_exp()))
            session_item.setText(4, "{:,}".format(combat_session.get_inf()))

    def repopulate(self, session):
        def set_styling(item, font_size=10, is_bold=False, background_color=None):
            for i in range(8):
                item.setFont(i, QFont("Arial", font_size, QFont.Bold if is_bold else QFont.Normal))
                if background_color:
                    item.setBackground(i, background_color)

        def create_character_item(tree_widget, character_name, duration):
            character_item = QTreeWidgetItem(tree_widget, [character_name])
            set_styling(character_item, font_size=11, is_bold=True, background_color=QColor(240, 240, 240))
            character_item.setData(1, Qt.DisplayRole, character.get_dps(duration))
            character_item.setData(2, Qt.DisplayRole, "{:,}%".format(character.get_accuracy()))
            character_item.setData(3, Qt.DisplayRole, "{:,}".format(character.get_average_damage()))
            character_item.setData(7, Qt.DisplayRole, "{:,}".format(character.get_total_damage()))

            character_item.setTextAlignment(2, Qt.AlignCenter)
            character_item.setTextAlignment(3, Qt.AlignCenter)
            character_item.setTextAlignment(4, Qt.AlignCenter)
            character_item.setTextAlignment(5, Qt.AlignCenter)
            character_item.setTextAlignment(6, Qt.AlignCenter)

            return character_item

        def create_ability_item(parent_item, ability_name, duration):
            ability_item = QTreeWidgetItem(parent_item, [ability_name])
            ability_item.setData(1, Qt.DisplayRole, ability.get_dps(duration))
            ability_item.setData(2, Qt.DisplayRole, "{:,}%".format(ability.get_accuracy()))
            ability_item.setData(3, Qt.DisplayRole, "{:,}".format(ability.get_average_damage()))
            ability_item.setData(4, Qt.DisplayRole, "{:,}".format(ability.get_count()))
            ability_item.setData(5, Qt.DisplayRole, "{:,}".format(ability.get_max_damage()))
            ability_item.setData(6, Qt.DisplayRole, "{:,}".format(ability.get_min_damage()))
            ability_item.setData(7, Qt.DisplayRole, "{:,}".format(ability.get_total_damage()))

            ability_item.setTextAlignment(2, Qt.AlignCenter)
            ability_item.setTextAlignment(3, Qt.AlignCenter)
            ability_item.setTextAlignment(4, Qt.AlignCenter)
            ability_item.setTextAlignment(5, Qt.AlignCenter)
            ability_item.setTextAlignment(6, Qt.AlignCenter)

            return ability_item

        def create_damage_item(parent_item, damage_name, duration):
            damage_item = QTreeWidgetItem(parent_item, [damage_name.name])
            damage_item.setData(1, Qt.DisplayRole,damage_name.get_dps(duration))
            damage_item.setData(3, Qt.DisplayRole, "{:,}".format(damage_name.get_average_damage()))
            damage_item.setData(4, Qt.DisplayRole, "{:,}".format(damage_name.get_count()))
            damage_item.setData(5, Qt.DisplayRole, "{:,}".format(damage_name.get_highest_damage()))
            damage_item.setData(6, Qt.DisplayRole, "{:,}".format(damage_name.get_lowest_damage()))
            

            damage_item.setTextAlignment(2, Qt.AlignCenter)
            damage_item.setTextAlignment(3, Qt.AlignCenter)
            damage_item.setTextAlignment(4, Qt.AlignCenter)
            damage_item.setTextAlignment(5, Qt.AlignCenter)
            damage_item.setTextAlignment(6, Qt.AlignCenter)

            return damage_item


        current_column = self.ability_tree_display.header().sortIndicatorSection()
        current_order = self.ability_tree_display.header().sortIndicatorOrder()
        self.ability_tree_display.clear()

        # Repopulate the treeWidget
        if session is None:
            return

        duration = session.duration

        for character_name, character in session.chars.items():
            character_item = create_character_item(self.ability_tree_display, character_name, duration)

            for ability_name, ability in character.abilities.items():
                ability_item = create_ability_item(character_item, ability_name, duration)

                for damage_name in ability.damage:
                    create_damage_item(ability_item, damage_name, duration)

        self.ability_tree_display.expandToDepth(0)
        self.ability_tree_display.sortByColumn(current_column, current_order)

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
    def unlock_ui(self):
        self.start_stop_button.setEnabled(True)
        self.process_button.setEnabled(True)
        self.file_path_var.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.run_test_button.setEnabled(True)
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
        self.ability_tree_display.clear()
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
        self.combat_session_data = test_sessions
        # Populate the tree with test data
        self.repopulate_sessions(self.combat_session_data)


if __name__ == "__main__":
    # Create the UI
    app = QApplication(sys.argv)
    ui = LogMonitorUI(parser=Parser())
    ui.show()
    sys.exit(app.exec_())