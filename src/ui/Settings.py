import sys
from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QSpinBox, QLineEdit, QVBoxLayout, QWidget, QPushButton, QCheckBox, QHBoxLayout
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

        layout = QVBoxLayout()

        # Combat Session Timeout
        tooltip = "The amount of time in seconds to wait after the last action before ending a combat session"
        timeout_label = QLabel("Combat Session Timeout:")
        timeout_label.setToolTip(tooltip)
        layout.addWidget(timeout_label)

        timeout_spinbox = QSpinBox()
        timeout_spinbox.setToolTip(tooltip)
        timeout_spinbox.setMinimum(0)
        timeout_spinbox.setMaximum(9999)
        timeout_spinbox.setValue(self.settings.value("CombatSessionTimeout", Globals.DEFAULT_COMBAT_SESSION_TIMEOUT, int))
        timeout_spinbox.valueChanged.connect(self.save_combat_session_timeout)
        layout.addWidget(timeout_spinbox)

        # Combat Session Name
        tooltip = "This is the default name for a combat session.  It can be overridden by in-game chat commands"
        name_label = QLabel("Default Session Name:")
        name_label.setToolTip(tooltip)
        layout.addWidget(name_label)

        name_lineedit = QLineEdit()
        name_lineedit.setToolTip(tooltip)
        name_lineedit.setText(self.settings.value("CombatSessionName", Globals.DEFAULT_COMBAT_SESSION_NAME, str))
        name_lineedit.textChanged.connect(self.save_combat_session_name)
        layout.addWidget(name_lineedit)

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
        layout.addLayout(proc_layout)

        # Console Verbosity
        tooltip = "The amount of information to display in the console - For Debug purposes only, this WILL impact performance"
        verbosity_label = QLabel("Console Verbosity:")
        verbosity_label.setToolTip(tooltip)
        layout.addWidget(verbosity_label)

        verbosity_spinbox = QSpinBox()
        verbosity_spinbox.setToolTip(tooltip)
        verbosity_spinbox.setMinimum(0)
        verbosity_spinbox.setMaximum(4)
        verbosity_spinbox.setValue(self.settings.value("ConsoleVerbosity", Globals.DEFAULT_CONSOLE_VERBOSITY, int))
        verbosity_spinbox.valueChanged.connect(self.save_console_verbosity)
        layout.addWidget(verbosity_spinbox)

        

        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)


        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
     

        button_layout = QHBoxLayout()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        # Widget to hold the layout
        widget = QWidget()
        widget.setLayout(layout)
        self.setLayout(layout)
        apply_stylesheet(self)

    def save_combat_session_timeout(self, value):
        self.settings.setValue("CombatSessionTimeout", value)

    def save_combat_session_name(self, text):
        self.settings.setValue("CombatSessionName", text)

    def save_console_verbosity(self, value):
        self.settings.setValue("ConsoleVerbosity", value)

    def save_associate_procs_to_powers(self, value):
        self.settings.setValue("AssociateProcsToPowers", value)
        
    def save_settings(self):
        self.settings.sync()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    sys.exit(app.exec_())
