from log_monitor_controller import LogMonitorController
from log_monitor_ui import LogMonitorUI
from parser_model import Parser

def main():
    parser = Parser()
    ui = LogMonitorUI()
    controller = LogMonitorController(parser, ui)
    ui.start()
    ui.display_results(parser.get_results())

if __name__ == "__main__":
    main()
