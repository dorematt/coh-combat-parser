import tkinter as tk
from tkinter import filedialog, ttk
from typing import Callable
from combat_parser import CombatSession

class LogMonitorUI(tk.Tk):
    monitoring_live = False


    def __init__(self, *args, **kwargs):
        # Initialization code here
        print("     Initializing UI...")
        super().__init__(*args, **kwargs)  # Call the superclass constructor
        self.title("Combat Log Parser")

        # Initialize UI Variables
        self.file_path_var = tk.StringVar(self)
        self.overall_dps_var = tk.StringVar(self)

        # Configure the grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        # Configure the grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # File path input label and entry
        self.file_path_label = tk.Label(self, text="Log File Path:")
        self.file_path_entry = tk.Entry(self, textvariable=self.file_path_var, width=50)
        self.browse_button = tk.Button(self, text="Browse", command=self.browse_file)

        # Start/Stop and Process buttons
        self.start_stop_button = tk.Button(self, text="Start/Stop Log", command=self.start_stop_log)
        self.process_button = tk.Button(self, text="Process Existing Log")

        # Run Test button to add test data to the Treeview
        self.run_test_button = tk.Button(self, text="Run Test", command=self.add_ability)


        # DPS label and variable display
        self.overall_dps_label = tk.Label(self, text="DPS:")
        self.overall_dps_display = tk.Label(self, textvariable=self.overall_dps_var)

        # Create a treeview to display all abilities and their DPS
  
        columns = ("Ability Name", "DPS", "Number of Hits", "Accuracy %", "Avg Damage per Hit", "Total Damage")
        self.ability_tree_display = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.ability_tree_display.heading(col, text=col)
            self.ability_tree_display.column(col, anchor=tk.CENTER)

        # Combat Session Tree
            columns = ("Combat Session")
        self.combat_session_tree = ttk.Treeview(self, columns=columns)
        

        # Add vertical scrollbar
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.ability_tree_display.yview)
        self.ability_tree_display.configure(yscrollcommand=self.scrollbar.set)



        # UI PLACEMENT ONTO GRID
        self.file_path_label.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        self.file_path_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self.browse_button.grid(row=0, column=2, padx=10, pady=10)

        self.start_stop_button.grid(row=1, column=0, padx=10, pady=10)
        self.process_button.grid(row=1, column=1, padx=10, pady=10)

        self.combat_session_tree.grid(row=2, column=0, columnspan=2, padx=10, pady=10)
        self.ability_tree_display.grid(row=2, column=2, columnspan=4, padx=10, pady=10, sticky='nsew')
        self.scrollbar.grid(row=2, column=7, sticky='ns')

        print("Done.")

    def exit(self):
        # Stop the UI
        self.destroy()
    
    # Function to browse and select a file
    def browse_file(self):
        file_path = filedialog.askopenfilename()
        self.file_path_var.set(file_path) 

    # Function to handle "Start/Stop Log" button click
    def start_stop_log(self):
        # If the button says "Start Log", start the log
        if self.start_stop_button['text'] == "Start Log":
            self.LogMonitorController.start_log_monitor(self.file_path_var.get(), self.on_new_log_entry)
            self.start_stop_button['text'] = "Stop Log"
            self.process_button['state'] = tk.DISABLED
            self.file_path_entry['state'] = tk.DISABLED
            self.browse_button['state'] = tk.DISABLED
            
        # If the button says "Stop Log", stop the log
        elif self.start_stop_button['text'] == "Stop Log":
            self.start_stop_button['text'] = "Start Log"
            self.process_button['state'] = tk.NORMAL
            self.file_path_entry['state'] = tk.NORMAL
            self.browse_button['state'] = tk.NORMAL
            self.LogMonitorController.stop_log_monitor()

    # Function to handle "Process Existing Log" button click
    def process_existing_log(self, callback):
        # If the button says "Process Existing Log", process the log
        if self.process_button['text'] == "Process Existing Log":
            self.process_button['text'] = "Stop Processing"
            self.start_stop_button['state'] = tk.DISABLED
            self.file_path_entry['state'] = tk.DISABLED
            self.browse_button['state'] = tk.DISABLED
            self.callback(self.file_path_var.get())

    def run_test_log(self):
        pass
        # Call the run_test_data method in the LogMonitorController
        self.LogMonitorController.run_test_data(self)


    def add_ability(self):
        # placeholder data for now, this will be replaced with data from the log_monitor_controller.py
        ability_data = ("New Ability", 150, 10, 90, 15, 1500)

        # Insert data into the Treeview
        self.ability_tree_display.insert("", "end", values=ability_data)
    
    def update_ui_combat_session(self, combat_session : CombatSession):
        '''Updates the tree with the latest combat session data, expects a CombatSession object as input'''''
        pass

if __name__ == "__main__":
    # Create the UI
    ui = LogMonitorUI()

    # Run the UI
    ui.add_ability()
    ui.mainloop()