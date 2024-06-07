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

# Folder Monitor Log
logging.basicConfig(filename=os.path.join(log_directory, 'folder_monitor.log'),
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# File Generation Log
file_generation_log_path = os.path.join(log_directory, 'file_generation.log')
file_generation_logger = logging.getLogger('file_generation_logger')
file_generation_logger.setLevel(logging.INFO)
file_generation_handler = logging.FileHandler(file_generation_log_path)
file_generation_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
file_generation_logger.addHandler(file_generation_handler)

EMAIL_ADDRESS = "071bfafc4dde91"
EMAIL_PASSWORD = "9918ecc6a25877"
CHECK_INTERVAL = 180  # Check every 5 minutes
MAX_ATTACHMENT_SIZE = 4 * 1024 * 1024  # 4 MB

class FolderMonitor:
    def __init__(self, directory, email, password):
        self.directory = directory
        self.email = email
        self.password = password
        logging.info("FolderMonitor initialized")

    def zip_file(self, file_path):
        try:
            if file_path.endswith('.zip'):
                logging.info(f"File {file_path} is already zipped, skipping.")
                return file_path

            zip_path = file_path + '.zip'
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.write(file_path, os.path.basename(file_path))
            os.remove(file_path)  # Delete the original file after zipping
            logging.info(f"Deleted original file: {file_path}")
            file_generation_logger.info(f"Generated zip file: {zip_path}")
            return zip_path
        except Exception as e:
            logging.error(f"Failed to zip file {file_path}: {e}")
            return None

    def get_folder_contents(self):
        contents = "Output folder contents:\n"
        try:
            for f in os.listdir(self.directory):
                file_path = os.path.join(self.directory, f)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    contents += f"{f} - {file_size / (1024 * 1024):.2f} MB\n"
        except Exception as e:
            logging.error(f"Failed to get folder contents: {e}")
        return contents

    def split_file(self, file_path):
        parts = []
        try:
            file_size = os.path.getsize(file_path)
            if file_size <= MAX_ATTACHMENT_SIZE:
                return [file_path]

            part_num = 1
            with open(file_path, 'rb') as f:
                while True:
                    part_data = f.read(MAX_ATTACHMENT_SIZE)
                    if not part_data:
                        break
                    part_path = f"{file_path}.prt{part_num}"
                    with open(part_path, 'wb') as part_file:
                        part_file.write(part_data)
                    parts.append(part_path)
                    part_num += 1
            os.remove(file_path)  # Remove the original file after splitting
        except Exception as e:
            logging.error(f"Failed to split file {file_path}: {e}")
        return parts

    def send_mail(self, email, password, subject, message, attachment_paths=None):
        total_sent = 0
        current_msg = MIMEMultipart()
        current_msg['From'] = email
        current_msg['To'] = email
        current_msg['Subject'] = subject

        try:
            # Read log files and add to the message
            with open(os.path.join(log_directory, 'folder_monitor.log'), 'r') as log_file:
                folder_monitor_log_content = log_file.read()
            with open(file_generation_log_path, 'r') as file_gen_log_file:
                file_generation_log_content = file_gen_log_file.read()

            # Get folder contents and add to the message
            folder_contents = self.get_folder_contents()

            email_body = (message + "\n\nLog entries from folder_monitor.log:\n" + folder_monitor_log_content +
                          "\n\nLog entries from file_generation.log:\n" + file_generation_log_content +
                          "\n\n" + folder_contents)
            current_msg.attach(MIMEText(email_body, 'plain'))

            if attachment_paths:
                attachment_paths.sort(key=os.path.getsize, reverse=True)  # Start with largest file to manage space

                for attachment_path in attachment_paths:
                    if os.path.exists(attachment_path):
                        file_size = os.path.getsize(attachment_path)
                        if file_size > MAX_ATTACHMENT_SIZE:
                            logging.info(f"File {attachment_path} exceeds 4MB and will be ignored.")
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

            # Clear the log files after sending the email
            with open(os.path.join(log_directory, 'folder_monitor.log'), 'w'):
                pass
            with open(file_generation_log_path, 'w'):
                pass
            logging.info("Log files cleared after sending email.")
        except Exception as e:
            logging.error(f"Failed to prepare email: {e}")

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
            try:
                files = [os.path.join(self.directory, f) for f in os.listdir(self.directory) if os.path.isfile(os.path.join(self.directory, f))]
                if files:
                    zipped_files = []
                    for file in files:
                        zip_path = self.zip_file(file)
                        if zip_path:
                            if os.path.getsize(zip_path) <= MAX_ATTACHMENT_SIZE:
                                zipped_files.append(zip_path)
                                logging.info(f"Zipped file: {file} to {zip_path}")
                            else:
                                split_files = self.split_file(zip_path)
                                zipped_files.extend(split_files)

                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    subject = f"Files Report - {timestamp}"
                    self.send_mail(self.email, self.password, subject, "Log of recent actions and file status:", zipped_files)
                    logging.info(f"Email with subject '{subject}' sent.")
            except Exception as e:
                logging.error(f"Error during folder check: {e}")

            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        # Send initial email indicating script has started
        initial_subject = "Script Started"
        initial_message = "The folder monitor script has started successfully."

        initial_msg = MIMEMultipart()
        initial_msg['From'] = EMAIL_ADDRESS
        initial_msg['To'] = EMAIL_ADDRESS
        initial_msg['Subject'] = initial_subject
        initial_msg.attach(MIMEText(initial_message, 'plain'))

        try:
            with smtplib.SMTP("smtp.mailtrap.io", 2525) as server:
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, initial_msg.as_string())
            logging.info("Initial email sent successfully.")
        except Exception as e:
            logging.error(f"Failed to send initial email: {e}")

        folder_monitor = FolderMonitor(output_directory, EMAIL_ADDRESS, EMAIL_PASSWORD)
        # Send initial email indicating script has started with folder contents
        initial_subject = "Folder Monitor Script Started"
        initial_message = "The folder monitor script has started successfully.\n\n" + folder_monitor.get_folder_contents()
        folder_monitor.send_mail(EMAIL_ADDRESS, EMAIL_PASSWORD, initial_subject, initial_message)
        folder_monitor.check_folder()
    except Exception as e:
        logging.error(f"Failed to start FolderMonitor: {e}")
