import sys
from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QSpinBox, QLineEdit, QVBoxLayout, QWidget, QPushButton, QCheckBox, QHBoxLayout, QComboBox, QGroupBox
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QIcon
from data.Globals import Globals
from ui.style.Theme import apply_stylesheet


class SettingsWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Settings")
        #self.setGeometry(100, 100, 300, 200)

        self.settings = QSettings(Globals.AUTHOR, Globals.APPLICATION_NAME)

        self.layout = QVBoxLayout()

        # Combat Session Timeout
        tooltip = "The amount of time in seconds to wait after the last action before ending a combat session"
        timeout_label = QLabel("Combat Session Timeout:")
        timeout_label.setToolTip(tooltip)
        self.layout.addWidget(timeout_label)

        timeout_spinbox = QSpinBox()
        timeout_spinbox.setToolTip(tooltip)
        timeout_spinbox.setMinimum(0)
        timeout_spinbox.setMaximum(9999)
        timeout_spinbox.setValue(self.settings.value("CombatSessionTimeout", Globals.DEFAULT_COMBAT_SESSION_TIMEOUT, int))
        timeout_spinbox.valueChanged.connect(self.save_combat_session_timeout)
        self.layout.addWidget(timeout_spinbox)



        #Associate Procs to Powers
        tooltip = "Toggle whether to associate procs to powers or make them their own ability"
        proc_label = QLabel("Associate Procs to Powers:")
        proc_label.setToolTip(tooltip)

        proc_checkbox = QCheckBox(checked=self.settings.value("AssociateProcsToPowers", Globals.DEFAULT_ASSOCIATE_PROCS_TO_POWERS, bool))
        proc_checkbox.setToolTip(tooltip)
        proc_checkbox.stateChanged.connect(self.save_associate_procs_to_powers)

        proc_layout = QHBoxLayout()
        proc_layout.addWidget(proc_label)
        proc_layout.addWidget(proc_checkbox)
        self.layout.addLayout(proc_layout)

        # Automatically update to latest file
        tooltip = "Automatically check and set the filepath to the latest log file"
        auto_update_label = QLabel("Get Latest Log File:")
        auto_update_label.setToolTip(tooltip)

        auto_update_checkbox = QCheckBox()
        auto_update_checkbox.setToolTip(tooltip)
        auto_update_checkbox.setChecked(self.settings.value("AutoUpdateLogFile", Globals.DEFAULT_AUTO_UPDATE_LOG_FILE, bool))
  
        auto_update_layout = QHBoxLayout()
        auto_update_layout.addWidget(auto_update_label)
        auto_update_layout.addWidget(auto_update_checkbox)
        self.layout.addLayout(auto_update_layout)
        
        # Console Verbosity
        tooltip = "The amount of information to display in the console - For Debug purposes only, this WILL impact performance"
        verbosity_label = QLabel("Console Verbosity:")
        verbosity_label.setToolTip(tooltip)
        self.layout.addWidget(verbosity_label)

        verbosity_spinbox = QSpinBox()
        verbosity_spinbox.setToolTip(tooltip)
        verbosity_spinbox.setMinimum(0)
        verbosity_spinbox.setMaximum(4)
        verbosity_spinbox.setValue(self.settings.value("ConsoleVerbosity", Globals.DEFAULT_CONSOLE_VERBOSITY, int))
        verbosity_spinbox.valueChanged.connect(self.save_console_verbosity)
        self.layout.addWidget(verbosity_spinbox)

        session_naming_group = QGroupBox("Default Session Naming")
        self.sesison_name_layout = QVBoxLayout(session_naming_group)
        self.layout.addLayout(self.sesison_name_layout)

        # Default Session Naming
        tooltip = "Sets the default naming behaviour for combat sessions"

        self.naming_combobox = QComboBox()
        self.naming_combobox.setToolTip(tooltip)
        self.naming_combobox.addItem("User Specified")
        self.naming_combobox.addItem("Player Name")
        self.naming_combobox.addItem("Timestamp")
        self.naming_combobox.addItem("First Enemy Damaged")
        self.naming_combobox.addItem("Highest Damaged Enemy")
        self.naming_combobox.setCurrentIndex(self.settings.value("DefaultSessionNaming", Globals.DEFAULT_COMBAT_SESSION_OPTION, int))
        self.naming_combobox.currentIndexChanged.connect(self.update_user_default_session_name)
        self.sesison_name_layout.addWidget(self.naming_combobox)

        # User Specified Name Prefix
        tooltip = "The prefix to use when naming a combat session with the User Specified naming behaviour"
        self.user_prefix_label = QLabel("User Specified Name:")
        self.user_prefix_label.setToolTip(tooltip)   
        self.sesison_name_layout.addWidget(self.user_prefix_label)

        self.user_prefix_lineedit = QLineEdit()
        self.user_prefix_lineedit.setToolTip(tooltip)
        self.user_prefix_lineedit.setText(self.settings.value("UserSpecifiedNamePrefix", Globals.DEFAULT_COMBAT_SESSION_NAME, str))
        self.user_prefix_lineedit.textChanged.connect(self.update_user_prefix)
        if self.naming_combobox.currentIndex() != 0:
            self.user_prefix_lineedit.setEnabled(False)
            self.user_prefix_lineedit.setVisible(False)
            self.user_prefix_label.setVisible(False)
        self.sesison_name_layout.addWidget(self.user_prefix_lineedit)

        self.layout.addWidget(session_naming_group)


        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)


        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
     

        button_layout = QHBoxLayout()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        self.layout.addLayout(button_layout)

        # Widget to hold the layout
        widget = QWidget()
        widget.setLayout(self.layout)
        self.setLayout(self.layout)
        apply_stylesheet(self)

    def save_combat_session_timeout(self, value):
        self.settings.setValue("CombatSessionTimeout", value)


    def save_console_verbosity(self, value):
        self.settings.setValue("ConsoleVerbosity", value)

    def save_associate_procs_to_powers(self, value):
        self.settings.setValue("AssociateProcsToPowers", value)

    def save_auto_update_log_file(self, value):
        self.settings.setValue("AutoUpdateLogFile", value)
    
    def update_user_default_session_name(self, index):
        if index == 0:
            self.user_prefix_lineedit.setEnabled(True)
            self.user_prefix_lineedit.setVisible(True)
            self.user_prefix_label.setVisible(True)
        else:
            self.user_prefix_lineedit.setEnabled(False)
            self.user_prefix_lineedit.setVisible(False)
            self.user_prefix_label.setVisible(False)
            
        self.settings.setValue("DefaultSessionNaming", self.naming_combobox.currentIndex())
        #print ("User Selected Index: ", self.settings.value("DefaultSessionNaming", Globals.DEFAULT_COMBAT_SESSION_OPTION, int))

    def update_user_prefix(self, text):
        self.settings.setValue("UserSpecifiedNamePrefix", text)
        
    def save_settings(self):
        self.settings.sync()
        self.close()

if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    sys.exit(app.exec_())
