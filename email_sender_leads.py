import csv
import time
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os

load_dotenv()

email_password = os.environ.get('EMAIL_PASSWORD')
sender_email = os.environ.get('SENDER_EMAIL')

# Read the email body
with open('email.txt', 'r', encoding='utf-8') as file:
    content = file.read()

# Read email list from CSV
with open('emails.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    #next(reader)
    emails = [row[2] for row in reader if len(row) >= 3]  

batch_size = 20
total_emails = len(emails)

for i, email in enumerate(emails):
    if i % batch_size == 0:
        if 'server' in locals():
            try:
                server.quit()
                time.sleep(20)  # wait 20s between batches
            except:
                pass
        try:
            server = smtplib.SMTP_SSL('smtpout.secureserver.net', 465)
            server.login(sender_email, email_password)
            print(f"\n🔄 SMTP connection refreshed (batch {i // batch_size + 1})")
        except Exception as e:
            print(f"❌ Failed to reconnect SMTP: {e}")
            break

    msg = EmailMessage()
    msg['Subject'] = "Strengthen Your Lab’s Research Skills with Hands-on DNA Sequence Analysis Training"
    msg['From'] = sender_email
    msg['To'] = email
    msg.set_content(content)

    # Attach the poster image
    with open('poster.png', 'rb') as img:
        img_data = img.read()
        msg.add_attachment(img_data, maintype='image', subtype='png', filename='poster.png')

    try:
        server.send_message(msg, to_addrs=[email])
        print(f"✅ Email sent to {email} ({i + 1}/{total_emails})")
    except Exception as e:
        with open('failed_emails.log', 'a') as log:
            log.write(f"{email} — {e}\n")
        print(f"❌ Failed to send to {email} — {e}")

    time.sleep(5)  # 5s delay between individual emails

try:
    server.quit()
except:
    pass

print("\n🎉 All emails processed.")
