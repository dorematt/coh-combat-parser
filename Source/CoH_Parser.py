class Globals:
    VERSION = "0.0.4"
    BUILD_DATE = "11 Jan 2024"
    BUILD_TYPE = "ALPHA"
    AUTHOR = "@10kVolts"
    APPLICATION_NAME = "coh-combat-parser"
    CONTRIBUTORS = []


    DEFAULT_COMBAT_SESSION_TIMEOUT = 15
    DEFAULT_COMBAT_SESSION_NAME = "Session"
    DEFAULT_ASSOCIATE_PROCS_TO_POWERS = True
    DEFAULT_CONSOLE_VERBOSITY = 1


def main():
    from ui.MainUI import MainUI
    from combat.CombatParser import Parser
    from PyQt5.QtWidgets import QApplication
    import sys

    def preamble():
        print("")
        print("=================================================")
        print("    CoH Combat Parser - ", Globals.VERSION, " - ", Globals.BUILD_DATE)
        print("=================================================")
        print("")
        if Globals.BUILD_TYPE == "ALPHA": print("NOTE: This is an ALPHA Version.  It is not feature complete, and is not stable.  Use at your own risk.")
        if Globals.BUILD_TYPE == "BETA": print("NOTE: This is an BETA Version.  It is not feature complete, and is not stable.  Use at your own risk.")
        if Globals.BUILD_TYPE == ("REL" or "RELEASE" or "Stable"): print("RELEASE (Stable) Version")
        print("")
        print("Author:", Globals.AUTHOR)
        print("Visit: https://github.com/dorematt/coh-combat-parser/ for more information. ")
        print("")
        print("-----------------------------------------------")
        print("")
    preamble()

    app = QApplication(sys.argv)
    main_ui = MainUI()

    main_ui.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
