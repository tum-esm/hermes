import csv
import psutil
import time
from datetime import datetime

# File to save the data
FILENAME = 'system_usage.csv'


# Get the current CPU and memory usage in percent
def get_system_usage():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    memory_usage = memory_info.percent
    memory_usage_abs = memory_info.used / (1024 * 1024)
    return cpu_usage, memory_usage, memory_usage_abs


# Write headers to CSV file
with open(FILENAME, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Timestamp', 'CPU Usage (%)', 'Memory Usage (%)', 'Memory Usage (MB)'])


# Function to write system usage to CSV file
def log_system_usage():
    while True:
        cpu_usage, memory_usage, memory_usage_abs = get_system_usage()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(FILENAME, mode='a', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow([timestamp, cpu_usage, memory_usage, memory_usage_abs])

        # Get the current time, and the current second of the minute
        now = datetime.now()
        current_second = now.second

        # Calculate the number of seconds to wait until the next 5-second mark, then sleep for that amount of time.
        # This is preferred over a simple time.sleep(5) to ensure there is no time drift over long periods.
        wait_time = (5 - (current_second % 5)) % 5
        if current_second == 0:
            wait_time = 5
        time.sleep(wait_time)
        print(f"Logged system usage at {timestamp}: CPU = {cpu_usage}%, Memory = {memory_usage}%, Memory (MB) = {memory_usage_abs}MB")


# Start logging
if __name__ == "__main__":
    log_system_usage()
