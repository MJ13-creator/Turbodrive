import smtplib
from email.mime.text import MIMEText


def send_email(to_email, subject, message):
    sender = "your_email@gmail.com"
    password = "your_app_password"

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender, password)
    server.send_message(msg)
    server.quit()