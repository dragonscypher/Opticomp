
import csv
import os
import datetime
import psutil

# Directory to save task list CSVs
TASKLIST_DIR = "."

# Ensure the directory exists
os.makedirs(TASKLIST_DIR, exist_ok=True)

def create_tasklist_csv():
    # File name with date
    filename = os.path.join(TASKLIST_DIR, f"tasklist_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
    
    # Gather process information
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["PID", "Name", "Status", "CPU%", "Memory%", "Create Time"])
        
        for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent', 'create_time']):
            try:
                writer.writerow([
                    proc.info['pid'],
                    proc.info['name'],
                    proc.info['status'],
                    proc.info['cpu_percent'],
                    proc.info['memory_percent'],
                    datetime.datetime.fromtimestamp(proc.info['create_time']).strftime("%Y-%m-%d %H:%M:%S")
                ])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass  # Some processes might terminate before we get their info

if __name__ == "__main__":
    create_tasklist_csv()
    print(f"Task list created in {TASKLIST_DIR}.")
