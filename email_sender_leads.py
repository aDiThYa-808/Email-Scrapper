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
with open('learners_email.txt', 'r', encoding='utf-8') as file:
    content = file.read()

# Read email list from CSV
with open('BB-email-database.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    emails = [row[0].strip() for row in reader if len(row) >= 1 and row[0].strip() != '']

batch_size = 20
total_emails = len(emails)

for i in range(0, total_emails, batch_size):
    batch = emails[i:i + batch_size]

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
    msg['Subject'] = "Deadline Extended: Register by August 5 – Certification in DNA Sequence Analysis (Online Training)"
    msg['From'] = sender_email
    msg['To'] = 'prasannabarcoding@gmail.com'
    msg['Bcc'] = ', '.join(batch)
    msg.set_content(content)

    # Attach the poster image
    with open('poster-2.jpg', 'rb') as img:
        img_data = img.read()
        msg.add_attachment(img_data, maintype='image', subtype='jpg', filename='poster-2.jpg')

    try:
        server.send_message(msg)
        print(f"✅ Batch sent to {len(batch)} recipients ({i + 1}–{i + len(batch)})")
    except Exception as e:
        with open('failed_emails.log', 'a') as log:
            for b in batch:
                log.write(f"{b} — {e}\n")
        print(f"❌ Failed batch ({i + 1}–{i + len(batch)}): {e}")

    time.sleep(10)  # Slight delay between batches

try:
    server.quit()
except:
    pass

print("\n🎉 All emails processed.")
