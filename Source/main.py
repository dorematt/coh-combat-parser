from log_monitor_controller import LogMonitorController
from log_monitor_ui import LogMonitorUI
from combat_parser import Parser

def main():
    parser = Parser()
    ui = LogMonitorUI()
    controller = LogMonitorController(parser, ui)


if __name__ == "__main__":
    ui = LogMonitorUI()
