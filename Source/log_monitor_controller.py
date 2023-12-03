from log_monitor_ui import LogMonitorUI
from parser_model import Parser

class LogMonitorController:
    def __init__(self):
        self.ui = LogMonitorUI(self)
        self.parser = Parser()
        self.ui.start()

    def process_existing_log(self, file_path):
        # Instruct the parser to process an existing log file
        self.parser.process_existing_log(file_path)
        # Update the UI with results
        self.ui.display_results(self.parser.get_results())

    def start_log_monitor(self, file_path):
        # Start monitoring a log file for new lines
        self.parser.start_monitoring(file_path)

    def stop_log_monitor(self):
        # Stop monitoring the log file
        self.parser.stop_monitoring()

    def on_new_log_entry(self, log_entry):
        # Handle new log entry event from the parser
        pass # Update the UI with new data

    def run_test_data(self):
            sample_log_lines = [
        '2023-11-18 14:49:48 Readying Void Total Radial Judgement.\n',
        '2023-11-18 14:49:48 Sweet Radiation heals you with their Ground Zero for 9.37 health points over time.\n',
        '2023-11-18 14:49:49 You hit Lattice with your Degenerative Interface for 12.03 points of Toxic damage over time.\n',
        '2023-11-18 14:49:49 Thorn has defeated Jack Frost\n',
        '2023-11-18 14:49:49 You Stun Lattice with your Inky Aspect.\n',
        '2023-11-18 14:49:49 Emet Selch hits you with their Inky Aspect for 4.72 points of unresistable Special damage.\n',
        '2023-11-18 14:49:49 MISSED Lattice!! Your Inky Aspect power had a 95.00% chance to hit, you rolled a 95.27.\n',
        '2023-11-18 14:49:49 Sweet Radiation heals you with their Ground Zero for 9.37 health points over time.\n',
        '2023-11-18 14:49:51 You hit Lattice with your Void Total Radial Judgement for 641.12 points of Negative Energy damage.\n',
        '2023-11-18 14:49:51 You hit Lattice with your Doublehit for 38.91 points of Energy damage.\n',
        '2023-11-18 14:49:53 HIT Lattice! Your Black Dwarf Mire power had a 95.00% chance to hit, you rolled a 68.99.\n',
        '2023-11-18 14:50:03 Lattice MISSES! Crystal Shards power had a 11.25% chance to hit, but rolled a 62.66.\n',
        '2023-11-18 14:49:57 You hit Lattice with your Dark Nova Bolt for 264.55 points of Negative Energy damage.\n',
        '2023-11-18 14:49:58 Thorn HITS you! Thorn power had a 95.00% chance to hit and rolled a 22.43.\n',
        '2023-11-18 14:49:57 You are healed by your Power Transfer: Chance to Heal Self for 91.03 health points.\n',
        '2023-11-18 14:50:04 Emet Selch hits you with their Performance Shifter: Chance for +Endurance granting you 11 points of endurance.\n',
        '2023-11-18 14:50:07 HIT Lattice! Your Dark Detonation power was forced to hit by streakbreaker.'
    ]
            self.parser.run_test_data(sample_log_lines, self.parser.PATTERNS)     

if __name__ == "__main__":
    controller = LogMonitorController()