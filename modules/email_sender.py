"""
Free Email Outreach Engine using Gmail SMTP / Standard SMTP.
Supports auto-attaching promotional poster/flyer (codube.com) with Abhishek Jain.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import Dict, Any, Optional

DEFAULT_POSTER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "agency_poster.png")

def test_smtp_connection(smtp_user: str, smtp_pass: str, smtp_host: str = "smtp.gmail.com", smtp_port: int = 587) -> Dict[str, Any]:
    """
    Validates SMTP credentials with a test connection.
    """
    if not smtp_user or not smtp_pass:
        return {"success": False, "error": "SMTP Email or Password is blank."}
        
    try:
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_user.strip(), smtp_pass.strip().replace(" ", ""))
        server.quit()
        return {"success": True, "message": "SMTP Connection Successful! Ready to send emails as Abhishek Jain (codube.com)."}
    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "error": "Authentication failed! Make sure 2-Step Verification is ON in your Google Account and you generated an 'App Password'."
        }
    except Exception as e:
        return {"success": False, "error": f"SMTP Error: {str(e)}"}

def send_cold_email(
    to_email: str,
    subject: str,
    body: str,
    smtp_user: str,
    smtp_pass: str,
    sender_name: str = "Abhishek Jain | codube.com",
    poster_path: Optional[str] = DEFAULT_POSTER_PATH,
    smtp_host: str = "smtp.gmail.com",
    smtp_port: int = 587
) -> Dict[str, Any]:
    """
    Sends a personalized cold outreach email via SMTP, automatically attaching the agency poster.
    """
    if not to_email or "@" not in to_email:
        return {"success": False, "error": f"Invalid recipient email: {to_email}"}
        
    try:
        msg = MIMEMultipart("related")
        msg["From"] = f"{sender_name} <{smtp_user}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        
        # HTML body with inline poster if available
        html_formatted = body.replace("\n", "<br>")
        
        has_poster = poster_path and os.path.exists(poster_path)
        img_tag = '<br><br><img src="cid:agency_poster" style="max-width: 600px; width: 100%; border-radius: 8px; border: 1px solid #e2e8f0;"><br>' if has_poster else ""
        
        html_content = f"""
        <html>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 15px; color: #1e293b; line-height: 1.6;">
                <p>{html_formatted}</p>
                {img_tag}
                <hr style="border: 0; border-top: 1px solid #cbd5e1; margin: 25px 0;">
                <p style="font-size: 13px; color: #64748b;">
                    <strong>Abhishek Jain</strong> | Software Developer<br>
                    <strong>codube.com</strong> — Software Development & AI Business Automation Agency<br>
                    Website: <a href="https://codube.com" style="color: #0284c7;">codube.com</a>
                </p>
            </body>
        </html>
        """
        
        msg_alternative = MIMEMultipart("alternative")
        msg.attach(msg_alternative)
        
        # Plain text version
        msg_alternative.attach(MIMEText(body, "plain", "utf-8"))
        # HTML version
        msg_alternative.attach(MIMEText(html_content, "html", "utf-8"))
        
        # Attach image inline if exists
        if has_poster:
            try:
                with open(poster_path, "rb") as f:
                    img_data = f.read()
                img = MIMEImage(img_data)
                img.add_header("Content-ID", "<agency_poster>")
                img.add_header("Content-Disposition", "inline", filename=os.path.basename(poster_path))
                msg.attach(img)
            except Exception as img_err:
                print(f"Warning: could not attach poster image: {img_err}")
        
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=12)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_user.strip(), smtp_pass.strip().replace(" ", ""))
        server.sendmail(smtp_user, [to_email], msg.as_string())
        server.quit()
        
        return {"success": True, "message": f"Email successfully sent to {to_email} with poster attached!"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}
