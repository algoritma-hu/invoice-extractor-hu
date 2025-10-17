import os, smtplib
from email.mime.text import MIMEText

def send_email(summary_rows, cfg):
    if not cfg["notify"]["enabled"]:
        return
    body = "Processed documents:\n\n" + "\n".join(
        f"- {r.get('doc_type','?')}: {r.get('file','?')} -> {r.get('dest','?')}" for r in summary_rows
    )
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "Middleware Demo — Processing Summary"
    msg["From"] = cfg["notify"]["mail_from"]
    msg["To"] = cfg["notify"]["mail_to"]

    password = os.environ.get(cfg["notify"]["password_env"], "")
    if not password:
        raise RuntimeError(f"Missing env var {cfg['notify']['password_env']} for SMTP password")

    with smtplib.SMTP(cfg["notify"]["smtp_host"], cfg["notify"]["smtp_port"]) as s:
        if cfg["notify"]["use_tls"]:
            s.starttls()
        s.login(cfg["notify"]["username"], password)
        s.send_message(msg)
