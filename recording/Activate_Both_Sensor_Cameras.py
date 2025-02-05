import subprocess
import signal
import time
import os

# Paths to the scripts
scripts = {
    "Realsense Recorder": "/home/airlab5/Desktop/realsense_bag_recorder.py",
    "Shimmer Recorder": "/home/airlab5/Desktop/Shimmer_edited.py"
}

# Function to send SIGINT to a subprocess
def send_sigint(proc, name):
    if proc and proc.poll() is None:  # Check if subprocess is still running
        print(f"Stopping {name}...")
        proc.send_signal(signal.SIGINT)

# Start subprocesses
processes = {}
for name, path in scripts.items():
    if os.path.exists(path):
        print(f"Starting {name}...")
        processes[name] = subprocess.Popen(['python3', path])
    else:
        print(f"Error: {path} not found!")

try:
    # Keep running until both processes exit
    while any(proc.poll() is None for proc in processes.values()):
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nKeyboardInterrupt detected! Stopping all subprocesses...")
    for name, proc in processes.items():
        send_sigint(proc, name)

# Wait for subprocesses to exit
for name, proc in processes.items():
    proc.wait()
    print(f"{name} exited.")

print("All processes have stopped.")

