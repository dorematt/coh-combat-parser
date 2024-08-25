class Globals:
    import os
    VERSION = "0.1.2"
    BUILD_DATE = "11 Aug 2024"
    BUILD_TYPE = "ALPHA"
    AUTHOR = "@10kVolts"
    APPLICATION_NAME = "coh-combat-parser"
    CONTRIBUTORS = []

    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    DEFAULT_COMBAT_SESSION_TIMEOUT = 15
    DEFAULT_COMBAT_SESSION_OPTION = 0
    DEFAULT_COMBAT_SESSION_NAME = "Session"
    DEFAULT_ASSOCIATE_PROCS_TO_POWERS = True
    DEFAULT_CONSOLE_VERBOSITY = 1
    DEFAULT_AUTO_UPDATE_LOG_FILE = True
    USE_GUI_THEME = True

    NO_HIT_ABILITIES = ["Interface", "Shifting Tides"]