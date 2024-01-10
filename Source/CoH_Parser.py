from LogMonitorUI import LogMonitorUI
from CombatParser import Parser
from PyQt5.QtWidgets import QApplication
import sys
VERSION = "0.0.2"
BUILD_DATE = "10 Jan 2024"
BUILD_TYPE = "ALPHA"
AUTHOR = "@10kVolts"
CONTRIBUTORS = []
def main():

    def preamble():
        print("")
        print("=================================================")
        print("    CoH Combat Parser - ", VERSION, " - ", BUILD_DATE)
        print("=================================================")
        print("")
        if BUILD_TYPE == "ALPHA": print("NOTE: This is an ALPHA Version.  It is not feature complete, and is not stable.  Use at your own risk.")
        if BUILD_TYPE == "BETA": print("NOTE: This is an BETA Version.  It is not feature complete, and is not stable.  Use at your own risk.")
        if BUILD_TYPE == ("REL" or "RELEASE" or "Stable"): print("RELEASE (Stable) Version")
        print("")
        print("Author:", AUTHOR)
        print("Visit: https://github.com/dorematt/coh-combat-parser/ for more information. ")
        print("")
        print("-----------------------------------------------")
        print("")
    preamble()
    #parser = Parser()
    app = QApplication(sys.argv)
    main_ui = LogMonitorUI()

    main_ui.show()

    sys.exit(app.exec_())
if __name__ == "__main__":
    main()

