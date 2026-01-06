class Globals:
    import os
    VERSION = "0.2.0"
    BUILD_DATE = "6 Jan 2026"
    BUILD_TYPE = "BETA"
    AUTHOR = "@10kVolts"
    APPLICATION_NAME = "coh-combat-parser"
    CONTRIBUTORS = []

    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    DEFAULT_COMBAT_SESSION_TIMEOUT = 15
    DEFAULT_COMBAT_SESSION_NAME = "Session"
    DEFAULT_COMBAT_SESSION_NAMING_MODE = "Custom Name"  # Options: "First Enemy Damaged", "Highest Enemy Damaged", "Custom Name"
    DEFAULT_ASSOCIATE_PROCS_TO_POWERS = True
    DEFAULT_CONSOLE_VERBOSITY = 1
    DEFAULT_AUTO_UPDATE_LOG_FILE = True