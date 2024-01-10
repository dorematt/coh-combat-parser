from log_monitor_ui import LogMonitorUI
from combat_parser import Parser
from PyQt5.QtWidgets import QApplication
import sys

def main():
    parser = Parser()
    app = QApplication(sys.argv)
    main_ui = LogMonitorUI(parser)

    main_ui.show()

    sys.exit(app.exec_())
if __name__ == "__main__":
    main()

