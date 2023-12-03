import time
import tkinter as tk
from tkinter import filedialog
import threading
from queue import Queue
import re

class LogMonitor:
    def __init__(self, master):
        '''Creates the UI elements and variables for the Log Monitor window, should spin this into a separate function eventually'''
        self.master = master
        master.title("Log Monitor")

        #initialise variables
        self.keyword = ""
        self.log_running = False
        self.line_generator = None
        self.log_queue = Queue()
        self.log_thread = None
        self.start_time = 0  # Variable to store the start tim
        self.hits = 0
        self.misses = 0
        

        self.file_path_label = tk.Label(master, text="File Path:")
        self.file_path_label.grid(row=0, column=0, padx=5, pady=5)

        self.file_path_var = tk.StringVar()
        self.file_path_entry = tk.Entry(master, textvariable=self.file_path_var, width=40)
        self.file_path_entry.grid(row=0, column=1, padx=5, pady=5)

        self.browse_button = tk.Button(master, text="Browse", command=self.browse_button_click)
        self.browse_button.grid(row=0, column=2, padx=5, pady=5)

        self.start_log_button = tk.Button(master, text="Start Log", command=self.start_log)
        self.start_log_button.grid(row=0, column=3, padx=5, pady=5)

        self.stop_log_button = tk.Button(master, text="Stop Log", command=self.stop_log)
        self.stop_log_button.grid(row=0, column=4, padx=5, pady=5)
        self.stop_log_button["state"] = tk.DISABLED  # Initially disabled

        # Move these labels and entry fields under the File path and buttons
        self.keyword_label = tk.Label(master, text="Keyword:")
        self.keyword_label.grid(row=1, column=0, padx=5, pady=5)

        self.keyword_var = tk.StringVar()
        self.keyword_var.set("Chance for .* Damage")
        self.keyword_entry = tk.Entry(master, textvariable=self.keyword_var, width=20)
        self.keyword_entry.grid(row=1, column=1, padx=5, pady=5)

        self.counter_label = tk.Label(master, text="Counter:")
        self.counter_label.grid(row=1, column=2, padx=5, pady=5)

        self.counter_var = tk.IntVar()
        self.counter_var.set(0)
        self.counter_display = tk.Label(master, textvariable=self.counter_var)
        self.counter_display.grid(row=1, column=3, padx=5, pady=5)

        self.total_damage_label = tk.Label(master, text="Total Damage:")
        self.total_damage_label.grid(row=1, column=4, padx=5, pady=5)

        self.total_damage_var = tk.DoubleVar()
        self.total_damage_var.set(0)
        self.total_damage_display = tk.Label(master, textvariable=self.total_damage_var)
        self.total_damage_display.grid(row=1, column=5, padx=5, pady=5)

        self.total_time_label = tk.Label(master, text="Total Time (s):")
        self.total_time_label.grid(row=2, column=4, padx=5, pady=5)

        self.total_time_var = tk.IntVar()
        self.total_time_var.set(0)
        self.total_time_display = tk.Label(master, textvariable=self.total_time_var)
        self.total_time_display.grid(row=2, column=5, padx=5, pady=5)

        self.dps_label = tk.Label(master, text="DPS:")
        self.dps_label.grid(row=2, column=0)

        self.dps_var = tk.DoubleVar()
        self.dps_var.set(0.0)
        self.dps_display = tk.Label(master, textvariable=self.dps_var)
        self.dps_display.grid(row=2, column=1)
        
        self.accuracy_var = tk.DoubleVar()
        self.accuracy_label = tk.Label(master,text="Accuracy:")
        self.accuracy_label.grid(row=2, column=2, padx=2, pady=5)
        self.accuracy_display = tk.Label(master,textvariable=self.accuracy_var)
        self.accuracy_display.grid(row=2, column=3, padx=2, pady=5)

        self.average_per_hit_var = tk.DoubleVar()
        self.average_per_hit_var.set(0.0)
        self.average_per_hit_label = tk.Label(master, text="Average per hit: ")
        self.average_per_hit_label.grid(row=3, column=0)
        
        self.average_per_hit_display = tk.Label(master, textvariable=self.average_per_hit_var)
        self.average_per_hit_display.grid(row=3, column=1)

        # Make the text field scrollable
        self.log_text = tk.Text(master, height=10, width=75)
        self.log_text.grid(row=4, column=0, columnspan=10)

        # Add a scrollbar to make the text field scrollable
        scrollbar = tk.Scrollbar(master, command=self.log_text.yview)
        scrollbar.grid(row=4, column=10, sticky='nsew')
        self.log_text.config(yscrollcommand=scrollbar.set)

    def browse_button_click(self):
        init_dir = r'H:\Games\Homecoming_COH\accounts\10kVolts\Logs'  
        self.file_path_var.set(self.browse_file(init_dir))

    def browse_file(self, init_dir):
        file_path = filedialog.askopenfilename(title="Select Log File", filetypes=[("Text files", "*.txt")], initialdir=init_dir)
        if file_path:
            return file_path
        return None

    def logging_thread(self, file_path):
        with open(file_path, "r") as f:
            f.seek(0, 2)
            while self.log_running:
                line = f.readline()
                if not line:
                    time.sleep(0.01)
                    continue
                self.log_queue.put(line)

    def match_keyword(self, line):
        keyword = self.keyword_var.get()
        try:
            if re.search(keyword, line):
                found_text = f"Found: {line.strip()}\n"
                self.log_text.insert(tk.END, found_text)
                self.log_text.see(tk.END)
                self.counter_var.set(self.counter_var.get() + 1)
        except re.error:
            print("Invalid keyword regex pattern")

    def calculate_total_damage(self, line):

        '''Handles the total damage output by the user.
        It has a hard-coded damage pattern that identifies lines from the log that is the user dealing damage
        some exclusion strings are included for powers that hit yourself such as Inky Aspect'''

        damage_pattern = re.compile(r'.* You hit .* (\d+\.\d+) points of .* damage')
        damage_match = damage_pattern.search(line)

        
        # Define a list of strings to exclude from damage calculations
        damage_exclusion_strings = ["Inky Aspect", "Oppressive Gloom"]

        if damage_match and not any(exclusion_string in line for exclusion_string in damage_exclusion_strings):
            damage_value = float(damage_match.group(1))
            self.total_damage_var.set(round(self.total_damage_var.get()))
            self.total_damage_var.set(self.total_damage_var.get() + round(damage_value, 2))

    def calculate_total_time(self):
        if not self.start_time:
            self.start_time = time.time()
        else:
            self.total_time_var.set(round(time.time() - self.start_time))

    def calculate_dps(self):
        total_damage = self.total_damage_var.get()
        total_time = self.total_time_var.get()
        if total_time > 0:
            dps = round(total_damage / total_time, 2)
            self.dps_var.set(dps)
    def calculate_accuracy(self, line):
        hit_pattern_1 = re.compile(r'.*HIT.*Your.*had a.*, you rolled a.*')
        hit_pattern_2 = re.compile(r'.*HIT.*Your.*forced to hit by streakbreaker.*')
        miss_pattern = re.compile(r'.*MISSED.*Your.*had a.*, you rolled a.*')

        # Check if the line is a hit based on either pattern
        if hit_pattern_1.search(line) or hit_pattern_2.search(line):
            self.hits += 1
        # Check if the line is a miss
        elif miss_pattern.search(line):
            self.misses += 1

    def calculate_accuracy_percentage(self):
        total_hits_misses = self.hits + self.misses
        if total_hits_misses > 0:
            accuracy_percentage = (self.hits / total_hits_misses) * 100.0
            self.accuracy_var.set(round(accuracy_percentage, 2))
        else:
            self.accuracy_var.set(0.0)

    def calculate_average_per_hit(self):

        if self.hits > 0:
            average_per_hit = self.total_damage_var.get() / self.hits
            self.average_per_hit_var.set(round(average_per_hit, 2))
        else:
            self.average_per_hit_var.set(0.0)


    def monitor_log(self):
        try:
            if not self.log_queue.empty():
                line = self.log_queue.get_nowait()
                self.match_keyword(line)
                self.calculate_total_damage(line)
                self.calculate_total_time()
                self.calculate_dps()
                self.calculate_accuracy(line)
                self.calculate_accuracy_percentage()
                self.calculate_average_per_hit()
            if self.log_running:
                self.master.after(10, self.monitor_log)
        except Exception as e:
            print(f"An error occurred in monitor_log: {e}")
            # Handle other exceptions if needed

    def start_log(self):
        path = self.file_path_var.get()

        if not path:
            path = self.browse_file()

        if path:
            self.file_path_var.set(path)
            self.log_running = True
            self.start_log_button["state"] = tk.DISABLED
            self.stop_log_button["state"] = tk.NORMAL

            self.keyword = self.keyword_var.get()
            self.counter_var.set(0)
            self.total_damage_var.set(0)
            self.hits = 0
            self.misses = 0
            self.start_time = None  # Re-initialize start_time

            self.log_thread = threading.Thread(target=self.logging_thread, args=(path,))
            self.log_thread.start()

            self.master.after(100, self.monitor_log)

    def stop_log(self):
        self.log_running = False
        if self.log_thread:
            self.log_thread.join()
        self.start_log_button["state"] = tk.NORMAL
        self.stop_log_button["state"] = tk.DISABLED

    # ... (rest of your code)

if __name__ == "__main__":
    root = tk.Tk()
    app = LogMonitor(root)
    root.mainloop()