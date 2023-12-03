import tkinter as tk
from tkinter import filedialog, ttk
from typing import Callable

class LogMonitorUI(tk.Tk):
    # Create the main application window
    root = tk.Tk()
    root.title("Combat Log Parser")

    # Configure the grid
    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(1, weight=1)

    # Add UI components
    file_path_var = tk.StringVar(root)
    overall_dps_var = tk.StringVar(root)


    # Function to browse and select a file
    def browse_file():
        file_path = filedialog.askopenfilename()
        file_path_var.set(file_path)

    # Function to handle "Start/Stop Log" button click
    def start_stop_log():
        # If the button says "Start Log", start the log
        if start_stop_button['text'] == "Start Log":
            start_stop_button['text'] = "Stop Log"
            process_button['state'] = tk.DISABLED
            file_path_entry['state'] = tk.DISABLED
            browse_button['state'] = tk.DISABLED
            LogMonitorController.start_log_monitor(file_path_var.get())
        # If the button says "Stop Log", stop the log
        elif start_stop_button['text'] == "Stop Log":
            start_stop_button['text'] = "Start Log"
            process_button['state'] = tk.NORMAL
            file_path_entry['state'] = tk.NORMAL
            browse_button['state'] = tk.NORMAL
            LogMonitorController.stop_log_monitor()

    # Function to handle "Process Existing Log" button click
    def process_existing_log():
        # If the button says "Process Existing Log", process the log
        if process_button['text'] == "Process Existing Log":
            process_button['text'] = "Stop Processing"
            start_stop_button['state'] = tk.DISABLED
            file_path_entry['state'] = tk.DISABLED
            browse_button['state'] = tk.DISABLED
            LogMonitorController.process_existing_log(file_path_var.get())

    def run_test_log():
        # Call the run_test_data method in the LogMonitorController
        LogMonitorController.run_test_data()


    def add_ability(self):
        # placeholder data for now, this will be replaced with data from the log_monitor_controller.py
        ability_data = ("New Ability", 150, 10, 90, 15, 1500)

        # Insert data into the Treeview
        self.tree.insert("", "end", values=ability_data)

    # File path input label and entry
    file_path_label = tk.Label(root, text="Log File Path:")
    file_path_entry = tk.Entry(root, textvariable=file_path_var, width=50)
    browse_button = tk.Button(root, text="Browse", command=browse_file)

    # Start/Stop and Process buttons
    start_stop_button = tk.Button(root, text="Start/Stop Log", command=start_stop_log)
    process_button = tk.Button(root, text="Process Existing Log", command=process_existing_log)

    # Run Test button to add test data to the Treeview
    run_test_button = tk.Button(root, text="Run Test", command=add_ability)


    # DPS label and variable display
    overall_dps_label = tk.Label(root, text="DPS:")
    overall_dps_display = tk.Label(root, textvariable=overall_dps_var)

    # Create a treeview to display all abilities and their DPS
    columns = ("Ability Name", "DPS", "Number of Hits", "Accuracy %", "Avg Damage per Hit", "Total Damage")
    ability_tree_display = ttk.Treeview(root, columns=columns, show="headings")
    for col in columns:
        ability_tree_display.heading(col, text=col)
        ability_tree_display.column(col, anchor=tk.CENTER)

    # Add vertical scrollbar
    scrollbar = tk.Scrollbar(root, orient="vertical", command=ability_tree_display.yview)
    ability_tree_display.configure(yscrollcommand=scrollbar.set)

    # Pack Treeview and Scrollbar
    ability_tree_display.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')
    scrollbar.grid(row=2, column=3, sticky='ns')


    # Place the components on the grid
    file_path_label.grid(row=0, column=0, padx=10, pady=10)
    file_path_entry.grid(row=0, column=1, padx=10, pady=10, sticky='ew')
    browse_button.grid(row=0, column=2, padx=10, pady=10)

    start_stop_button.grid(row=1, column=0, padx=10, pady=10)
    process_button.grid(row=1, column=1, padx=10, pady=10)


    # Run the main application loop
    root.mainloop()