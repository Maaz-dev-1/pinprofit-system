"""
Email Service — Gmail SMTP.
Sends all 12 notification types as defined in agent instructions.
"""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

logger = logging.getLogger(__name__)


async def send_email(
    gmail: str,
    password: str,
    to: str,
    subject: str,
    html_body: str,
) -> bool:
    """Send an HTML email via Gmail SMTP."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"PinProfit <{gmail}>"
        msg["To"]      = to
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail, password)
            server.sendmail(gmail, to, msg.as_string())

        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False


def _base_template(title: str, body: str) -> str:
    """Create branded HTML email template."""
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{ font-family: Inter, Arial, sans-serif; background: #1A0A10; color: #F8E8F0; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 0 auto; padding: 24px; }}
    .header {{ background: #E8426A; padding: 20px 24px; border-radius: 16px 16px 0 0; }}
    .header h1 {{ margin: 0; font-size: 20px; color: white; }}
    .body {{ background: #2A1520; padding: 24px; border-radius: 0 0 16px 16px; border: 1px solid #3D1F2A; }}
    .footer {{ text-align: center; margin-top: 16px; font-size: 12px; color: #C4899E; }}
    a {{ color: #E8426A; }}
    .btn {{ display: inline-block; background: #E8426A; color: white !important; text-decoration: none; padding: 12px 24px; border-radius: 12px; font-weight: bold; margin-top: 16px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header"><h1>📌 PinProfit</h1></div>
    <div class="body">
      <h2>{title}</h2>
      {body}
    </div>
    <div class="footer">
      PinProfit &mdash; Your Automated Affiliate Pin System<br>
      <a href="#">Open App</a> &middot; <a href="#">Unsubscribe</a>
    </div>
  </div>
</body>
</html>"""


async def send_research_started(gmail, password, to, niche):
    await send_email(gmail, password, to,
        f"Research Started — {niche}",
        _base_template("Research Started! 🔍", f"""
        <p>Your research for <strong>'{niche}'</strong> has started.</p>
        <p>This will take 30–60 minutes. You don't need to keep the app open.</p>
        <p>We'll notify you when it's done with product recommendations ready for pinning.</p>
        """))


async def send_research_complete(gmail, password, to, niche, product_count, top_products):
    products_html = "".join(
        f"<li><strong>{p.get('title', '')[:60]}...</strong> — Score: {p.get('score', 0)} — {p.get('platform', '').title()}</li>"
        for p in top_products[:3]
    )
    await send_email(gmail, password, to,
        f"[{product_count}] Products Found! Research Complete 🎉",
        _base_template(f"Research Complete! {product_count} Products Found", f"""
        <p>Research for <strong>'{niche}'</strong> is done!</p>
        <p>We found <strong>{product_count} high-scoring products</strong>.</p>
        <p><strong>Top 3 picks:</strong></p>
        <ul>{products_html}</ul>
        <a href="#" class="btn">Open App to Create Pins →</a>
        """))
