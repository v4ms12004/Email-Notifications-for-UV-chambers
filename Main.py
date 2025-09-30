#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import smtplib
import imaplib
import email
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# =========================
# ======  CONFIG   ========
# =========================
SENDER_EMAIL   = "projectnotification25@gmail.com"   # account that SENDS alerts (and whose INBOX we read)
RECEIVER_EMAIL = "vamsi.d.2004@gmail.com"            # recipient of alerts (the one who replies)
GMAIL_APP_PWD  = "kpke bpge lvml ymzi"  # set env var in your OS
FILE_PATH      = "Mail/UV Log 1.txt"                 # path to the log (updates ~1 minute)

INTERVAL_SECONDS = 10                                 # check cadence (spam hot every 10s)
STATUS_UPDATE_EVERY = 4 * 60 * 60                     # every 4 hours (seconds)

# Temperature thresholds
TEMP_HOT_MIN         = 70.0  # > 70°F = HOT (spam every loop)
TEMP_COLD_MAX        = 40.0  # < 40°F = COLD (one-time per episode)
COLD_CLEAR_THRESHOLD = 42.0  # both temps must exceed this to re-arm cold email

# Humidity thresholds
HUM_LOW_MAX          = 15.0  # < 15% RH = LOW HUMIDITY (one-time per episode)
HUM_CLEAR_THRESHOLD  = 17.0  # both hum must be >= this to re-arm low-humidity email

# Pause settings (reply by email)
MIN_PAUSE_MINUTES = 1  # enforce minimum pause length

# =========================
# ======  HELPERS   =======
# =========================

def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def parse_latest_row(path: str) -> Optional[List[str]]:
    """
    Returns [date, time, hum1, hum2, temp1, temp2] or None.
    Tries tab-split first, then whitespace. Robust to AM/PM and extra punctuation.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
    except FileNotFoundError:
        print(f"[{ts()}] File not found: {path}")
        return None
    except Exception as e:
        print(f"[{ts()}] Error reading file: {e}")
        return None

    if not lines:
        return None

    last_line = lines[-1]
    if "\t" in last_line:
        row = [tok.strip() for tok in last_line.split("\t")]
    else:
        tokens = re.split(r"\s+", last_line.strip())
        if len(tokens) >= 6:
            hum1, hum2, temp1, temp2 = tokens[-4:]
            head = tokens[:-4]
            if len(head) >= 2:
                date = head[0]
                time_field = " ".join(head[1:])
                row = [date, time_field, hum1, hum2, temp1, temp2]
            else:
                print(f"[{ts()}] Unrecognized line format: {tokens}")
                return None
        else:
            print(f"[{ts()}] Unrecognized line format: {tokens}")
            return None

    if len(row) != 6:
        print(f"[{ts()}] Parsed row is not length 6: {row}")
        return None
    return row

def any_hot(row: List[str]) -> bool:
    try:
        t1 = float(row[4]); t2 = float(row[5])
        return (t1 > TEMP_HOT_MIN) or (t2 > TEMP_HOT_MIN)
    except Exception:
        return False

def classify_cold_state(row: List[str]) -> str:
    t1 = float(row[4]); t2 = float(row[5])
    b1 = t1 < TEMP_COLD_MAX
    b2 = t2 < TEMP_COLD_MAX
    if b1 and b2:
        return "both_cold"
    if b1:
        return "box1_cold"
    if b2:
        return "box2_cold"
    return "safe"

def cold_has_cleared(row: List[str]) -> bool:
    t1 = float(row[4]); t2 = float(row[5])
    return (t1 > COLD_CLEAR_THRESHOLD) and (t2 > COLD_CLEAR_THRESHOLD)

def classify_low_hum_state(row: List[str]) -> str:
    h1 = float(row[2]); h2 = float(row[3])
    b1 = h1 < HUM_LOW_MAX
    b2 = h2 < HUM_LOW_MAX
    if b1 and b2:
        return "both_lowhum"
    if b1:
        return "box1_lowhum"
    if b2:
        return "box2_lowhum"
    return "safe"

def low_hum_has_cleared(row: List[str]) -> bool:
    h1 = float(row[2]); h2 = float(row[3])
    return (h1 >= HUM_CLEAR_THRESHOLD) and (h2 >= HUM_CLEAR_THRESHOLD)

def box_status(temp: float, hum: float) -> str:
    t_stat = "HOT" if temp > TEMP_HOT_MIN else ("COLD" if temp < TEMP_COLD_MAX else "NORMAL")
    h_stat = "LOW" if hum < HUM_LOW_MAX else "NORMAL"
    return f"Temp: {t_stat} ({temp:.1f}°F), Humidity: {h_stat} ({hum:.1f}%)"

# ---------- Email sending ----------

def _send_email(subject: str, body: str) -> None:
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SENDER_EMAIL, GMAIL_APP_PWD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    except Exception as e:
        print(f"[{ts()}] SMTP Error: {e}")

def send_hot_email(row: List[str], alert_number: int) -> None:
    t1 = float(row[4]); t2 = float(row[5])
    if t1 > TEMP_HOT_MIN and t2 > TEMP_HOT_MIN:
        status = "Both Boxes are HOT!"
    elif t1 > TEMP_HOT_MIN:
        status = "Box 1 is HOT!"
    else:
        status = "Box 2 is HOT!"

    extra = ""
    if float(row[2]) < HUM_LOW_MAX or float(row[3]) < HUM_LOW_MAX:
        extra = " (Note: low humidity present)"
    elif (t1 < TEMP_COLD_MAX) or (t2 < TEMP_COLD_MAX):
        extra = " (Note: the other box is COLD)"
    elif (40.0 <= t1 <= TEMP_HOT_MIN) or (40.0 <= t2 <= TEMP_HOT_MIN):
        extra = " (Note: the other box is NORMAL)"

    subject = f"⚠️ HOT Alert #{alert_number}"
    body = (
        f"{status}{extra}\n\n"
        f"Date:  {row[0]}\n"
        f"Time:  {row[1]}\n"
        f"Hum1:  {row[2]}%\n"
        f"Hum2:  {row[3]}%\n"
        f"Temp1: {row[4]}°F\n"
        f"Temp2: {row[5]}°F\n"
        f"\nReply with '15', '1h 30m', etc. to pause alerts.\n"
        f"This will continue every {INTERVAL_SECONDS}s while HOT.\n"
    )
    _send_email(subject, body)
    print(f"[{ts()}] 📧 HOT alert email sent.")

def send_cold_email_once(row: List[str]) -> None:
    state = classify_cold_state(row)
    if state == "both_cold":
        status = "Both Boxes are COLD!"
    elif state == "box1_cold":
        status = "Box 1 is COLD!"
    elif state == "box2_cold":
        status = "Box 2 is COLD!"
    else:
        status = "Temperature Alert (cold)"

    subject = "❄️ COLD Alert (one-time for this episode)"
    body = (
        f"{status}\n\n"
        f"Date:  {row[0]}\n"
        f"Time:  {row[1]}\n"
        f"Hum1:  {row[2]}%\n"
        f"Hum2:  {row[3]}%\n"
        f"Temp1: {row[4]}°F\n"
        f"Temp2: {row[5]}°F\n"
        f"\nFurther cold emails suppressed until BOTH temps exceed {COLD_CLEAR_THRESHOLD:.1f}°F.\n"
    )
    _send_email(subject, body)
    print(f"[{ts()}] 📧 Cold alert email sent (one-time).")

def send_low_hum_email_once(row: List[str]) -> None:
    state = classify_low_hum_state(row)
    if state == "both_lowhum":
        status = "Both Boxes have LOW HUMIDITY!"
    elif state == "box1_lowhum":
        status = "Box 1 has LOW HUMIDITY!"
    elif state == "box2_lowhum":
        status = "Box 2 has LOW HUMIDITY!"
    else:
        status = "Humidity Alert (low)"

    subject = "🌵 LOW HUMIDITY Alert (one-time for this episode)"
    body = (
        f"{status}\n\n"
        f"Date:  {row[0]}\n"
        f"Time:  {row[1]}\n"
        f"Hum1:  {row[2]}%\n"
        f"Hum2:  {row[3]}%\n"
        f"Temp1: {row[4]}°F\n"
        f"Temp2: {row[5]}°F\n"
        f"\nFurther low-humidity emails suppressed until BOTH humidities are ≥ {HUM_CLEAR_THRESHOLD:.1f}%.\n"
    )
    _send_email(subject, body)
    print(f"[{ts()}] 📧 Low-humidity alert email sent (one-time).")

def send_status_update(row: Optional[List[str]]) -> None:
    """
    Sends a Status Update email summarizing both boxes.
    """
    subject = "Status Update"
    if not row:
        body = (
            f"Status update at {ts()}.\n\n"
            f"No valid reading available from the log file.\n"
        )
    else:
        h1 = float(row[2]); h2 = float(row[3])
        t1 = float(row[4]); t2 = float(row[5])
        b1 = box_status(t1, h1)
        b2 = box_status(t2, h2)
        body = (
            f"Status update at {ts()} (Last record: {row[0]} {row[1]}):\n\n"
            f"Box 1 — {b1}\n"
            f"Box 2 — {b2}\n\n"
            f"Thresholds: HOT>{TEMP_HOT_MIN}°F, COLD<{TEMP_COLD_MAX}°F, LOW HUM<{HUM_LOW_MAX}%.\n"
        )
    _send_email(subject, body)
    print(f"[{ts()}] 📨 Status Update email sent.")

# ---------- Pause parsing (robust to quoted replies) ----------

def _parse_duration_to_minutes(text: str) -> Optional[int]:
    if not text:
        return None
    text = text.lower()

    m_full = re.fullmatch(r'\s*(\d{1,5})\s*', text)
    if m_full:
        return int(m_full.group(1))

    hours = sum(int(x) for x in re.findall(r'(\d+)\s*h', text))
    mins  = sum(int(x) for x in re.findall(r'(\d+)\s*(?:m|min|mins|minute|minutes)\b', text))
    secs  = sum(int(x) for x in re.findall(r'(\d+)\s*(?:s|sec|secs|second|seconds)\b', text))
    if hours or mins or secs:
        return max(hours * 60 + mins + (secs // 60), 0)
    return None

def _strip_reply_and_noise(body: str) -> str:
    if not body:
        return ""
    body = body.replace('\r\n', '\n').replace('\r', '\n')
    cutoff_patterns = [
        r'^On .+ wrote:', r'^From:', r'^Sent:', r'^Subject:', r'^To:', r'^Cc:',
        r'^-----Original Message-----', r'^_{5,}',
    ]
    lines = []
    for line in body.split('\n'):
        if any(re.match(pat, line.strip(), flags=re.IGNORECASE) for pat in cutoff_patterns):
            break
        if line.strip().startswith('>'):
            continue
        lines.append(line)
    top = '\n'.join(lines).strip()
    top = re.sub(r'\b\d{1,2}:\d{2}(:\d{2})?\b', ' ', top)                      # times
    top = re.sub(r'\b\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?\b', ' ', top)            # dates
    top = re.sub(r'\b(\d{1,2})\s*(am|pm)\b', ' ', top, flags=re.IGNORECASE)    # am/pm
    top = '\n'.join(top.splitlines()[:5])[:400]
    return top.strip()

def _parse_unitless_minutes_from_user_text(text: str) -> Optional[int]:
    if not text:
        return None
    cand_re = r'(?<![:/\-\d])\b(\d{1,4})\b(?![:/\-\d])'
    cands = []
    for m in re.finditer(cand_re, text):
        n = int(m.group(1)); pos = m.start()
        if 1 <= n <= 720:
            cands.append((pos, n))
    if cands:
        cands.sort(key=lambda x: x[0])
        return cands[0][1]
    any_ints = [int(x) for x in re.findall(r'\b(\d{1,5})\b', text[:400])]
    any_in_range = [n for n in any_ints if 1 <= n <= 720]
    if any_in_range:
        return any_in_range[0]
    return None

def _get_first_text_part(msg: email.message.Message) -> str:
    if msg.is_multipart():
        plain = []
        html  = None
        for part in msg.walk():
            ctype = part.get_content_type()
            disp  = part.get_content_disposition()
            if disp == 'attachment':
                continue
            if ctype == 'text/plain':
                payload = part.get_payload(decode=True) or b''
                plain.append(payload.decode(errors='ignore'))
            elif ctype == 'text/html' and html is None:
                payload = part.get_payload(decode=True) or b''
                html = payload.decode(errors='ignore')
        if plain:
            return '\n'.join(plain)
        if html:
            return re.sub(r'<[^>]+>', ' ', html)
        return ""
    else:
        payload = msg.get_payload(decode=True) or b""
        return payload.decode(errors="ignore")

def read_pause_minutes_from_inbox(sender_address: str, password: str, filter_from: str) -> Optional[int]:
    IMAP_SERVER = "imap.gmail.com"
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(sender_address, password)
    except imaplib.IMAP4.error as e:
        print(f"[{ts()}] IMAP login error: {e}")
        return None

    minutes_found = None
    try:
        mail.select("inbox")
        status, email_ids = mail.search(None, f'(UNSEEN FROM "{filter_from}")')
        if status != "OK":
            print(f"[{ts()}] IMAP search failed")
            mail.logout()
            return None

        ids = email_ids[0].split()
        if not ids:
            mail.logout()
            return None

        for email_id in reversed(ids):  # check newest first
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            if status != "OK":
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject = msg.get("Subject", "") or ""
            minutes = _parse_duration_to_minutes(subject)

            if minutes is None:
                body_text = _get_first_text_part(msg)
                user_top = _strip_reply_and_noise(body_text)
                minutes = _parse_duration_to_minutes(user_top) or _parse_unitless_minutes_from_user_text(user_top)

            mail.store(email_id, "+FLAGS", "\\Seen")

            if minutes is not None:
                minutes_found = minutes
                break

    except Exception as e:
        print(f"[{ts()}] IMAP error: {e}")
    finally:
        try:
            mail.logout()
        except:
            pass

    if minutes_found is not None and minutes_found < MIN_PAUSE_MINUTES:
        minutes_found = MIN_PAUSE_MINUTES
    return minutes_found

# =========================
# ========  MAIN  =========
# =========================

if __name__ == "__main__":
    cold_alert_active = False
    low_hum_alert_active = False
    hot_alert_count = 0

    paused_until_ts: Optional[float] = None  # non-blocking pause (alerts suppressed until this epoch)
    next_status_update_ts: float = time.time() + STATUS_UPDATE_EVERY

    print(f"[{ts()}] Monitor started. Checking every {INTERVAL_SECONDS}s. Press Ctrl+C to stop.")
    while True:
        try:
            # Check for pause requests via unread emails FROM receiver → sender
            pause_minutes = read_pause_minutes_from_inbox(SENDER_EMAIL, GMAIL_APP_PWD, RECEIVER_EMAIL)
            if pause_minutes is not None:
                pause_seconds = pause_minutes * 60
                now = time.time()
                paused_until_ts = max(paused_until_ts or 0, now + pause_seconds)
                until_str = datetime.fromtimestamp(paused_until_ts).strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{ts()}] Alerts paused for {pause_minutes} minute(s) (until {until_str}).")

            row = parse_latest_row(FILE_PATH)

            # Always send periodic Status Update (even while paused)
            now = time.time()
            if now >= next_status_update_ts:
                send_status_update(row)
                # schedule next
                next_status_update_ts = now + STATUS_UPDATE_EVERY

            alerts_paused = paused_until_ts is not None and now < paused_until_ts

            if not row:
                print(f"[{ts()}] No valid row found — skipping alerts this cycle.")
            else:
                if alerts_paused:
                    print(f"[{ts()}] Alerts are paused. Skipping HOT/COLD/HUM alerts this cycle.")
                else:
                    # HOT takes priority and spams every 10s
                    if any_hot(row):
                        hot_alert_count += 1
                        print(f"[{ts()}] 🔥 HOT condition — sending HOT email (spam mode). Count={hot_alert_count}")
                        send_hot_email(row, hot_alert_count)
                    else:
                        sent_any = False

                        # LOW HUMIDITY (one-time per episode)
                        hum_state = classify_low_hum_state(row)
                        if hum_state != "safe":
                            if not low_hum_alert_active:
                                print(f"[{ts()}] 🌵 Low humidity — sending one-time email.")
                                send_low_hum_email_once(row)
                                low_hum_alert_active = True
                                sent_any = True
                            else:
                                print(f"[{ts()}] 🌵 Low humidity ongoing — email already sent (no spam).")
                        else:
                            if low_hum_alert_active and low_hum_has_cleared(row):
                                low_hum_alert_active = False
                                print(f"[{ts()}] 🔄 Low-humidity episode cleared — re-armed.")

                        # COLD (one-time per episode)
                        cold_state = classify_cold_state(row)
                        if cold_state != "safe":
                            if not cold_alert_active:
                                print(f"[{ts()}] ❄️ Cold condition — sending one-time email.")
                                send_cold_email_once(row)
                                cold_alert_active = True
                                sent_any = True
                            else:
                                print(f"[{ts()}] ❄️ Cold ongoing — email already sent (no spam).")
                        else:
                            if cold_alert_active and cold_has_cleared(row):
                                cold_alert_active = False
                                print(f"[{ts()}] 🔄 Cold episode cleared — re-armed.")

                        if not sent_any and hum_state == "safe" and cold_state == "safe":
                            print(f"[{ts()}] ✅ Safe/normal reading.")

        except KeyboardInterrupt:
            print(f"\n[{ts()}] Stopping monitor. Bye!")
            break
        except Exception as e:
            print(f"[{ts()}] Processing error: {e}")

        time.sleep(INTERVAL_SECONDS)
