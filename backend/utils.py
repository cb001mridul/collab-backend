from passlib.context import CryptContext
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import bcrypt
import secrets


pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash(password: str):
    return pwd_context.hash(password)


def verify(plain_password,hashed_password):
    return pwd_context.verify(plain_password,hashed_password)


def generate_verification_token() -> str:

    return secrets.token_urlsafe(32)


def send_verification_email(email:str,verification_token: str):

    gmail_user = "collabgroup36@gmail.com"
    gmail_password = "xvvo xqoi vlld sstn"

    subject = "Account Verification"

    body = f"Greetings user, we are glad that you will now be going to become a part of a fastastic journey. You are just one step away. Click the following link to verify your email: http://your-app-url/verify-email/{verification_token}"
    
    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body,'plain'))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, email, msg.as_string())