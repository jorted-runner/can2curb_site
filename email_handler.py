import os
from email.message import EmailMessage
import ssl
import smtplib
from dotenv import load_dotenv

class EmailHandler:
    def __init__(self):
        load_dotenv()
        self.email_sender = os.environ.get('GMAIL')
        self.email_password = os.environ.get('GMAIL_CODE')

    def send_email(self, email_receiver, subject, body, bcc_receiver=None):
        em = EmailMessage()
        em['From'] = self.email_sender
        em['To'] = email_receiver
        em['Subject'] = subject
        em.set_content('Enable HTML to view the full email.')
        em.add_alternative(body, subtype='html')

        context = ssl.create_default_context()

        all_recipients = [email_receiver]
        if bcc_receiver:
            all_recipients.append(bcc_receiver)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(self.email_sender, self.email_password)
            smtp.sendmail(self.email_sender, all_recipients, em.as_string())
