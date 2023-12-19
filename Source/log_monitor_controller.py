from log_monitor_ui import LogMonitorUI
from combat_parser import Parser

class LogMonitorController:
    parser = None
    ui = None
    def __init__(self, ui, parser):
        print("Initializing Log Monitor Controller")
        self.parser = parser
        self.ui = ui
        print("DEBUG")
         

    def _bind(self) -> None:
        # self.ui.browse_button.bind("<Button-1>", self.browse_file)
        self.ui.start_stop_button.config(command=self.start_stop_log)
        self.ui.process_button.config(command=self.process_existing_log)
        self.ui.test_button.config(command=self.run_test_log)
        print("Bindings Done.")

    def process_existing_log(self, file_path):
        print("Processing existing log", file_path)
        self.ui.process_button['text'] = "Stop Processing"

        # Instruct the parser to process an existing log file
        self.parser.process_existing_log(file_path)
        # Update the UI with results
        #self.ui.display_results(self.parser.get_results())

    def start_log_monitor(self, file_path, callback):
        '''Start monitoring the log file for new entries.  When a new entry is found, issue a callback to the UI to update the UI with the new data'''
    
        # Check if the file path is valid
        if not self.parser.is_valid_file_path(file_path, callback):
            # If the file path is not valid, issue a callback to the UI to display an error
            callback(4) #Invalid Log File Path
            return
        self.parser.start_monitoring(file_path)
        # issue callback to update UI
        callback(-1)

    def stop_log_monitor(self, callback):
        # Stop monitoring the log file
        self.parser.stop_monitoring()
        # issue callback to update UI
        callback(-1)
        
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

    def run(self):
        print("Running Log Monitor Controller")
        self.mainloop()

if __name__ == "__main__":
    print("Log Monitor Controller  Running as __Main__")
    parser = Parser()
    ui = LogMonitorUI()
    controller = LogMonitorController(parser, ui)