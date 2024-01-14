import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QSpinBox, QLineEdit, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import QSettings
from CoH_Parser import Globals

class SettingsWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 300, 200)

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
        timeout_spinbox.setValue(self.settings.value("CombatSessionTimeout", 15, int))
        timeout_spinbox.valueChanged.connect(self.save_combat_session_timeout)
        layout.addWidget(timeout_spinbox)

        # Combat Session Name
        tooltip = "This is the default name for a combat session.  It can be overridden by in-game chat commands"
        name_label = QLabel("Default Session Name:")
        name_label.setToolTip(tooltip)
        layout.addWidget(name_label)

        name_lineedit = QLineEdit()
        name_lineedit.setToolTip(tooltip)
        name_lineedit.setText(self.settings.value("CombatSessionName", "Session"))
        name_lineedit.textChanged.connect(self.save_combat_session_name)
        layout.addWidget(name_lineedit)

        # Console Verbosity
        tooltip = "The amount of information to display in the console - For Debug purposes only, this WILL impact performance"
        verbosity_label = QLabel("Console Verbosity:")
        verbosity_label.setToolTip(tooltip)
        layout.addWidget(verbosity_label)

        verbosity_spinbox = QSpinBox()
        verbosity_spinbox.setToolTip(tooltip)
        verbosity_spinbox.setMinimum(0)
        verbosity_spinbox.setMaximum(4)
        verbosity_spinbox.setValue(self.settings.value("ConsoleVerbosity", 1, int))
        verbosity_spinbox.valueChanged.connect(self.save_console_verbosity)
        layout.addWidget(verbosity_spinbox)

        

        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

        # Widget to hold the layout
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def save_combat_session_timeout(self, value):
        self.settings.setValue("CombatSessionTimeout", value)

    def save_combat_session_name(self, text):
        self.settings.setValue("CombatSessionName", text)

    def save_console_verbosity(self, value):
        self.settings.setValue("ConsoleVerbosity", value)

    def save_settings(self):
        self.settings.sync()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    sys.exit(app.exec_())
