# 📬 Email Outreach Tool

A simple Python tool to automate cold outreach — from scraping emails to sending them.

## 🔧 Features

- **`email_scrapper.py`** – Scrapes email addresses from a website, including _obfuscated formats_ like `name at domain dot com`. Stores results in `emails.csv` *(auto-ignored via `.gitignore`)*  
- **`email_sender_leads.py`** – Sends a templated email (with optional attachments) to each contact in `emails.csv`

## ⚙️ Setup

1. **Clone the repo**

```bash
https://github.com/aDiThYa-808/email-outreach-tool.git
cd email-outreach-tool
```

2. **Create a `.env` file**

```
SENDER_EMAIL=you@example.com  
EMAIL_PASSWORD=yourpassword
```

3. **Install dependencies**

```bash
pip install python-dotenv
```

4. **Run the scripts**

```bash
# To scrape emails (handles obfuscation)
python email_scrapper.py

# To send emails
python email_sender_leads.py
```

## ✅ Notes

- `emails.csv` is `.gitignored` to avoid leaking scraped data.
- Batching and delays can be configured in `email_sender_leads.py` to avoid rate limits or blacklisting.
- Create `failed_emails.logs` to keep track of failed emails
- Uses secure SMTP connection via `smtplib`.
