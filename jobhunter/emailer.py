import os
import smtplib
from collections import Counter
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape


def _s(v):
    return escape(str(v or ""))


def build_html(rows):
    countries = Counter((r["country"] or r["location"] or "Unknown") for r in rows)
    buckets = {
        "90%+": sum(1 for r in rows if (r["match_score"] or 0) >= 90),
        "80-89%": sum(1 for r in rows if 80 <= (r["match_score"] or 0) < 90),
        "70-79%": sum(1 for r in rows if 70 <= (r["match_score"] or 0) < 80),
    }
    country_summary = " | ".join(f"{_s(k)}: {v}" for k, v in countries.most_common()) or "No new jobs"
    bucket_summary = " | ".join(f"{k}: {v}" for k, v in buckets.items())
    rows_html = []
    for r in rows:
        rows_html.append(f"""
        <tr>
          <td>{_s(r['title'])}</td><td>{_s(r['company'])}</td>
          <td>{_s(r['country'] or r['location'])}</td><td>{_s(r['remote_eligibility'] or r['remote_type'])}</td>
          <td>{_s(r['posted_at'])}</td><td><b>{_s(r['match_score'])}%</b></td>
          <td>{_s(r['matched_skills'])}</td><td>{_s(r['missing_skills'])}</td>
          <td>{_s(r['resume_suggestion'])}</td>
          <td><a href="{_s(r['url'])}">Apply</a></td>
        </tr>""")
    table = "".join(rows_html) if rows_html else '<tr><td colspan="10">No new matching jobs found in the last 24 hours.</td></tr>'
    return f"""
    <html><body style="font-family:Arial,sans-serif">
    <h2>Daily AI/ML Job Digest</h2>
    <p><b>New matching jobs:</b> {len(rows)}</p>
    <p>{country_summary}</p><p>{bucket_summary}</p>
    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-size:12px;width:100%">
      <thead><tr><th>Role</th><th>Company</th><th>Location</th><th>Remote eligibility</th><th>Posted</th><th>Match</th><th>Matched</th><th>Missing</th><th>Resume suggestion</th><th>Apply</th></tr></thead>
      <tbody>{table}</tbody>
    </table></body></html>"""


def send_email(rows, subject):
    host=os.getenv('SMTP_HOST'); port=int(os.getenv('SMTP_PORT','587'))
    username=os.getenv('SMTP_USERNAME'); password=os.getenv('SMTP_PASSWORD')
    sender=os.getenv('EMAIL_FROM'); recipient=os.getenv('EMAIL_TO')
    if not all([host,username,password,sender,recipient]):
        raise RuntimeError('Email credentials are not fully configured in .env')
    msg=MIMEMultipart('alternative'); msg['Subject']=subject; msg['From']=sender; msg['To']=recipient
    msg.attach(MIMEText(build_html(rows),'html'))
    with smtplib.SMTP(host,port,timeout=30) as server:
        server.starttls(); server.login(username,password); server.sendmail(sender,[recipient],msg.as_string())
    return recipient
