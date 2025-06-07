import smtplib
from email.message import EmailMessage

with open('email.txt', 'r') as file:
    email_content = file.read()

# Setup email parameters
msg = EmailMessage()
msg.set_content(email_content)
msg['Subject'] = "Automated Email: Absence Notification"
msg['From'] = "arnavashishshrma@gmail.com"
msg['To'] = "arnavashishsharma22@gmail.com"

# Login & send email using Gmail SMTP
with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login("arnavashishshrma@gmail.com", "lhvl cfdb hlaf qrqb")  # Use App Password, not Gmail password
    smtp.send_message(msg)

print("Email sent successfully!")
