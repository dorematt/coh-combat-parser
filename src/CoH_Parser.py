def main():
    '''
    Main entry point for the application.
    Initializes the UI and displays the main window.
    '''
    from ui.MainUI import MainUI
    from data.Globals import Globals
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
