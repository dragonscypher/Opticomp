import tkinter as tk
from tkinter import messagebox, ttk, Frame
import subprocess
import pandas as pd
import glob
import os
import psutil
import warnings
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from datetime import datetime

# Ignore non-critical warnings
warnings.filterwarnings("ignore")

# Function to execute and load the scripts automatically
def run_scripts():
    # Suppress warnings while running scripts
    subprocess.run(["python", "task_list_script.py"], stderr=subprocess.DEVNULL)
    subprocess.run(["python", "process_large_file_script.py"], stderr=subprocess.DEVNULL)
    subprocess.run(["python", "suggest_apps_script.py"], stderr=subprocess.DEVNULL)

# Function to suggest removable apps and allow user to terminate them
def suggest_removable_apps():
    try:
        # Load the latest removable apps suggestions
        removable_file = "removable_apps.csv"
        df = pd.read_csv(removable_file)

        # Clear previous data from TreeView
        for widget in content_frame.winfo_children():
            widget.destroy()

        suggestion_label = tk.Label(content_frame, text="Suggested Removable Apps:", font=("Arial", 14, "bold"), bg='#333333', fg='#ffffff')
        suggestion_label.pack(pady=10)

        # Treeview to display suggestions
        columns = ('Name', 'CPU%', 'Memory%')
        suggestion_tree = ttk.Treeview(content_frame, columns=columns, show='headings', height=8)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#444444", foreground="white", fieldbackground="#444444", font=("Arial", 10))
        style.configure("Treeview.Heading", background="#555555", foreground="white", font=("Arial", 12, "bold"))

        for col in columns:
            suggestion_tree.heading(col, text=col)
            suggestion_tree.column(col, minwidth=0, width=200, stretch=tk.NO)
        suggestion_tree.pack(pady=10, fill='both', expand=True)

        # Populate the TreeView
        if df.empty:
            suggestion_label.config(text="No removable apps found.")
        else:
            for _, row in df.iterrows():
                suggestion_tree.insert('', tk.END, values=(row['Name'], row['CPU%'], row['Memory%']))

        # Prompt user for confirmation to terminate any of these tasks
        def terminate_selected_tasks():
            selected_items = suggestion_tree.selection()
            for item in selected_items:
                task_name = suggestion_tree.item(item, 'values')[0]
                try:
                    for proc in psutil.process_iter(['pid', 'name']):
                        if proc.info['name'] == task_name:
                            proc.terminate()
                            print(f"Terminated process: {task_name}")
                            messagebox.showinfo("Terminated", f"Terminated process: {task_name}")
                except Exception as e:
                    print(f"Could not terminate {task_name}: {e}")
                    messagebox.showerror("Error", f"Could not terminate {task_name}: {e}")

        terminate_button = ttk.Button(content_frame, text="Terminate Selected Tasks", command=terminate_selected_tasks)
        terminate_button.pack(pady=10)

    except FileNotFoundError:
        messagebox.showerror("Error", "No removable apps file found.")
    except Exception as e:
        messagebox.showerror("Error", f"Unexpected error: {str(e)}")

# Function to display CPU and Memory usage of top 15 processes
def display_usage():
    # Load the most recent task list CSV file by timestamp
    list_of_files = glob.glob('tasklist_*.csv')
    if not list_of_files:
        messagebox.showerror("Error", "No task list files found.")
        return
    latest_file = max(list_of_files, key=os.path.getctime)
    try:
        df = pd.read_csv(latest_file)
        df = df[['Name', 'CPU%', 'Memory%']].dropna()  # Only keep relevant columns and drop any NaNs

        # Ensure values are in range of 100%
        df['CPU%'] = df['CPU%'].clip(upper=100)
        df['Memory%'] = df['Memory%'].clip(upper=100)

        # Sort by CPU and Memory usage, get the top 15
        top_memory = df.nlargest(15, 'Memory%')
        top_cpu = df.nlargest(15, 'CPU%')

        # Clear previous data from content_frame
        for widget in content_frame.winfo_children():
            widget.destroy()

        # Plotting Memory and CPU usage for top 15 processes side by side
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        fig.patch.set_facecolor('#2b2b2b')
        fig.subplots_adjust(wspace=0.4)

        # Customizing the plots
        # Memory Usage Plot
        ax1.barh(top_memory['Name'], top_memory['Memory%'], color='#FF6F61')  # Coral color for memory
        ax1.set_title("Top 15 Processes by Memory Usage", fontsize=14, weight='bold', color='#e0e0e0')
        ax1.set_xlabel("Memory Usage (%)", fontsize=10, color='#e0e0e0')
        ax1.set_ylabel("Process Name", fontsize=10, color='#e0e0e0')
        ax1.tick_params(axis='y', labelsize=8, colors='#e0e0e0')
        ax1.tick_params(axis='x', labelsize=8, colors='#e0e0e0')
        ax1.grid(True, linestyle='--', alpha=0.3)
        ax1.invert_yaxis()

        # CPU Usage Plot
        ax2.barh(top_cpu['Name'], top_cpu['CPU%'], color='#6A5ACD')  # Slate blue color for CPU
        ax2.set_title("Top 15 Processes by CPU Usage", fontsize=14, weight='bold', color='#e0e0e0')
        ax2.set_xlabel("CPU Usage (%)", fontsize=10, color='#e0e0e0')
        ax2.set_ylabel("Process Name", fontsize=10, color='#e0e0e0')
        ax2.tick_params(axis='y', labelsize=8, colors='#e0e0e0')
        ax2.tick_params(axis='x', labelsize=8, colors='#e0e0e0')
        ax2.grid(True, linestyle='--', alpha=0.3)
        ax2.invert_yaxis()

        # Embed the plot in Tkinter window
        canvas = FigureCanvasTkAgg(fig, master=content_frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack()

    except FileNotFoundError:
        messagebox.showerror("Error", "Processed data file not found.")
    except Exception as e:
        messagebox.showerror("Error", f"Unexpected error: {str(e)}")

# Run the scripts automatically when the application starts
run_scripts()

# UI setup
window = tk.Tk()
window.title("Process Optimizer")
window.geometry("1000x750")
window.configure(bg='#2b2b2b')  # Dark theme background

# Container to hold buttons at the top
top_frame = Frame(window, bg='#2b2b2b')
top_frame.pack(side='top', fill='x')

# Button style
button_style = ttk.Style()
button_style.theme_use("clam")
button_style.configure("TButton", padding=6, relief="flat", background="#ffffff", foreground="black", font=("Arial", 10, "bold"))
button_style.map("TButton",
                 foreground=[('pressed', 'black'), ('active', 'white')],
                 background=[('pressed', '!disabled', 'white'), ('active', '#666666')])

# Buttons to generate suggestions and display usage
ttk.Button(top_frame, text="Generate Suggestions", command=suggest_removable_apps).pack(side='left', padx=10, pady=10)
ttk.Button(top_frame, text="Display Usage", command=display_usage).pack(side='left', padx=10, pady=10)

# Container to display content based on user selection (suggestions or usage)
content_frame = Frame(window, bg='#3c3c3c', relief='groove', bd=2)
content_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)

# Start the UI loop
window.mainloop()
