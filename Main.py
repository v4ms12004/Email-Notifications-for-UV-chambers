import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import imaplib
import email
import time

# ---------- CONFIG ----------
sender_email = "projectnotification25@gmail.com"
receiver_email = "vamsi.d.2004@gmail.com"
password = "kpke bpge lvmu zmzi"  # Gmail App Password
file_path = "Mail/UV Log 1.txt"  # Path to your text file
# ----------------------------

def check_conditions(row):
    """
    row: list of values [date, time, hum1, hum2, temp1, temp2]
    Returns True if temperature is out of safe range.
    """
    try:
        hum1 = float(row[2])
        hum2 = float(row[3])
        temp1 = float(row[4])
        temp2 = float(row[5])
        if temp1 < 40 or temp1 > 70 or temp2 < 40 or temp2 > 70 or hum1 < 15 or hum2 < 15:
            return True
    except Exception:
        return False
    return False

def get_latest_row(path):
    """Reads the last non-empty line from the file and splits it by tab."""
    with open(path, "r") as file:
        lines = [line.strip() for line in file if line.strip()]
        #print(lines[-1])
        if not lines:
            return None
        last_line = lines[-1]
        # Try tab split first
        row = last_line.split("\t")
        #print(row)
        if len(row) == 1:
            # No tabs present; split on any whitespace sequence
            tokens = re.split(r"\s+", last_line.strip())
            # Handle a 7-token pattern where time and AM/PM are separated
            if len(tokens) == 7 and tokens[2] in ("AM", "PM"):
                date = tokens[0]
                time = tokens[1] + " " + tokens[2]  # combine time + AM/PM
                hum1, hum2, temp1, temp2 = tokens[3:]
                row = [date, time, hum1, hum2, temp1, temp2]
            elif len(tokens) == 6:
                row = tokens
            else:
                print(f"Unrecognized line format (tokens={len(tokens)}): {tokens}")
        #print(row)
        if len(row) == 6:
            return row
    return None

def send_email(row, alert_number):
    #case 1: Box 1 is hot, Box 2 is cold
    if float(row[4]) > 70 and float(row[5]) < 40:
        subject = f"⚠️ Temperature Alert {alert_number}"
        body = (
            "Box 1 is HOT!!!!!!! and Box 2 is COLD!!!!!!!:\n\n"
            f"Date: {row[0]}\n Time: {row[1]}\n Hum1: {row[2]}\n Hum2: {row[3]}\n "
            f"Temp1: {row[4]}\n Temp2: {row[5]}\n"
        )

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print("Email sent successfully!")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            server.quit()

    # Case 2: Box 1 is hot, Box 2 is fine
    elif float(row[4]) > 70 and float(row[5]) <= 70 and float(row[5]) >= 40:
        subject = f"⚠️ Temperature Alert {alert_number}"
        body = (
            "Box 1 is HOT!!!!!!!:\n\n"
            f"Date: {row[0]}\n Time: {row[1]}\n Hum1: {row[2]}\n Hum2: {row[3]}\n "
            f"Temp1: {row[4]}\n Temp2: {row[5]}\n"
        )

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print("Email sent successfully!")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            server.quit()

    #Case 3: Box 1 is hot, Box 2 is hot
    elif float(row[4]) > 70 and float(row[5]) > 70:
        subject = f"⚠️ Temperature Alert {alert_number}"
        body = (
            "Both Boxes are HOT!!!!!!!:\n\n"
            f"Date: {row[0]}\n Time: {row[1]}\n Hum1: {row[2]}\n Hum2: {row[3]}\n "
            f"Temp1: {row[4]}\n Temp2: {row[5]}\n"
        )

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print("Email sent successfully!")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            server.quit()

    #Case 4: Box 1 is fine, Box 2 is cold
    
    #elif float(row[5]) < 40 and float(row[4]) <= 70 and float(row[4]) >= 40:
    #    subject = f"⚠️ Temperature Alert {alert_number}"
    #    body = (
    #        "Box 2 is COLD!!!!!!!:\n\n"
    #        f"Date: {row[0]}\n Time: {row[1]}\n Hum1: {row[2]}\n Hum2: {row[3]}\n "
    #        f"Temp1: {row[4]}\n Temp2: {row[5]}\n"
    #    )

        #        msg = MIMEMultipart()
        #        msg["From"] = sender_email
        #        msg["To"] = receiver_email
        #        msg["Subject"] = subject
        #        msg.attach(MIMEText(body, "plain"))
        #
        #        try:
        #            server = smtplib.SMTP("smtp.gmail.com", 587)
        #            server.starttls()
        #            server.login(sender_email, password)
        #            server.sendmail(sender_email, receiver_email, msg.as_string())
        #            print("Email sent successfully!")
        #        except Exception as e:
        #            print(f"Error: {e}")
        #        finally:
        #            server.quit()
        #    #Case 5: Box 1 is fine, Box 2 is fine (safe case)
        #
        #    #Case 6: Box 1 is fine, Box 2 is hot
        #    elif float(row[5]) > 70 and float(row[4]) <= 70 and float(row[4]) >= 40:
        #        subject = f"⚠️ Temperature Alert {alert_number}"
        #        body = (
        #            "Box 2 is HOT!!!!!!!:\n\n"
        #            f"Date: {row[0]}\n Time: {row[1]}\n Hum1: {row[2]}\n Hum2: {row[3]}\n "
        #            f"Temp1: {row[4]}\n Temp2: {row[5]}\n"
        #        )
        #
        #        msg = MIMEMultipart()
        #        msg["From"] = sender_email
        #        msg["To"] = receiver_email
        #        msg["Subject"] = subject
        #        msg.attach(MIMEText(body, "plain"))
        #
        #        try:
        #            server = smtplib.SMTP("smtp.gmail.com", 587)
        #            server.starttls()
        #            server.login(sender_email, password)
        #            server.sendmail(sender_email, receiver_email, msg.as_string())
        #            print("Email sent successfully!")
        #        except Exception as e:
        #            print(f"Error: {e}")
        #        finally:
        #            server.quit()


    # #Case 7: Box 1 is cold, Box 2 is fine
    # elif float(row[4]) < 40 and float(row[5]) <= 70 and float(row[5]) >= 40:
    #     subject = f"⚠️ Temperature Alert {alert_number}"
    #     body = (
    #         "Box 1 is COLD!!!!!!!:\n\n"
    #         f"Date: {row[0]}\n Time: {row[1]}\n Hum1: {row[2]}\n Hum2: {row[3]}\n "
    #         f"Temp1: {row[4]}\n Temp2: {row[5]}\n"
    #     )
    #
    #     msg = MIMEMultipart()
    #     msg["From"] = sender_email
    #     msg["To"] = receiver_email
    #     msg["Subject"] = subject
    #     msg.attach(MIMEText(body, "plain"))
    #
    #     try:
    #         server = smtplib.SMTP("smtp.gmail.com", 587)
    #         server.starttls()
    #         server.login(sender_email, password)
    #         server.sendmail(sender_email, receiver_email, msg.as_string())
    #         print("Email sent successfully!")
    #     except Exception as e:
    #         print(f"Error: {e}")
    #     finally:
    #         server.quit()
    #
    # #Case 8: Box 1 is cold, Box 2 is cold
    # elif float(row[4]) < 40 and float(row[5]) < 40:
    #     subject = f"⚠️ Temperature Alert {alert_number}"
    #     body = (
    #         "Both Boxes are COLD!!!!!!!:\n\n"
    #         f"Date: {row[0]}\n Time: {row[1]}\n Hum1: {row[2]}\n Hum2: {row[3]}\n "
    #         f"Temp1: {row[4]}\n Temp2: {row[5]}\n"
    #     )
    #
    #     msg = MIMEMultipart()
    #     msg["From"] = sender_email
    #     msg["To"] = receiver_email
    #     msg["Subject"] = subject
    #     msg.attach(MIMEText(body, "plain"))
    #
    #     try:
    #         server = smtplib.SMTP("smtp.gmail.com", 587)
    #         server.starttls()
    #         server.login(sender_email, password)
    #         server.sendmail(sender_email, receiver_email, msg.as_string())
    #         print("Email sent successfully!")
    #     except Exception as e:
    #         print(f"Error: {e}")
    #     finally:
    #         server.quit()

def read_email(sender_address, password, email_address):
    IMAP_SERVER = 'imap.gmail.com' # e.g., 'imap.gmail.com' for Gmail
    EMAIL_ADDRESS = sender_address
    PASSWORD = password

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ADDRESS, PASSWORD)
    except imaplib.IMAP4.error as e:
        print(f"Error connecting or logging in: {e}")
        # Handle the error, e.g., exit or retry

    mail.select('inbox')

    # Search only unread emails from the specified sender
    SENDER_FILTER = email_address
    status, email_ids = mail.search(None, f'(UNSEEN FROM "{SENDER_FILTER}")')
    if status != 'OK':
        print("Search failed")
        mail.logout()
        return 0

    email_id_list = email_ids[0].split()
    if not email_id_list:
        print(f"No unread emails from {SENDER_FILTER}.")
        mail.logout()
        return None

    for email_id in email_id_list:
        status, msg_data = mail.fetch(email_id, '(RFC822)') # Fetch the full email content
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Access email details
        subject = msg.get('Subject', '(No Subject)')
        sender = msg.get('From', '(Unknown Sender)')
        date = msg.get('Date', '(No Date)')

        print(f"Subject: {subject}")
        print(f"From: {sender}")
        print(f"Date: {date}")

        # Get email body (handling multipart messages)
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = part.get_content_disposition()  # may be None
                if disposition == 'attachment':
                    continue
                if content_type == 'text/plain':
                    payload = part.get_payload(decode=True)
                    if payload:
                        print(f"Body (Plain Text):\n{payload.decode(errors='ignore')}")
                elif content_type == 'text/html':
                    payload = part.get_payload(decode=True)
                    if payload:
                        print(f"Body (HTML):\n{payload.decode(errors='ignore')}")
                # attachments skipped
        else:
            body = msg.get_payload(decode=True).decode()
            print(f"Body:\n{body}")

        # Optional: Mark email as seen
        mail.store(email_id, '+FLAGS', '\Seen')
        mail.logout()
        try:
            return int(subject.strip())
        except Exception:
            return None

    mail.logout()
    return None

if __name__ == "__main__":
    ATTEMPTS = 10
    INTERVAL_SECONDS = 10  # 10 seconds
    #Stop_Spamming = 600 #10 minutes
    for attempt in range(1, ATTEMPTS + 1):
        print(f"\nAttempt {attempt}/{ATTEMPTS}:")
        # Check for email from you before sending
        time_stop = read_email(sender_email, password, receiver_email)
        if time_stop is not None:
            Stop_Spamming = time_stop * 60
            print(f"Received email from you. Stopping further email notifications for {time_stop} minutes.")
            time.sleep(Stop_Spamming)
        latest_row = get_latest_row(file_path)
        if latest_row and check_conditions(latest_row):
            send_email(latest_row, attempt)
        else:
            print("✅ Latest record is within safe range. No email sent.")
        if attempt < ATTEMPTS:
            print(f"Waiting {INTERVAL_SECONDS} seconds before next check...")
            time.sleep(INTERVAL_SECONDS)
    print("\nFinished scheduled email checks.")
