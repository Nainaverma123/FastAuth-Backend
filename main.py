import email
from fastapi import FastAPI
from auth import create_access_token
from model.User import User
from model.Organization import Organization
from model.LoginRequest import LoginRequest
from model.EmailRequest import EmailRequest
from database import conn
from passlib.context import CryptContext
import smtplib
from email.mime.text import MIMEText
from fastapi.responses import Response
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

@app.get("/")
def home():
    return {"message": "Welcome to the Voxora AI Insights API!"}


@app.post("/users/")
def create_user(user: User):

    cursor = conn.cursor()

    hashed_password = pwd_context.hash(user.password)

    cursor.execute(
        """
        INSERT INTO users
        (username, email, password, role)
        VALUES (%s, %s, %s, %s)
        """,
        (
            user.username,
            user.email,
            hashed_password,
            user.role
        )
    )

    conn.commit()

    return {"message": "User created successfully!"}


@app.post("/organizations/")
def create_organization(org: Organization):

    cursor = conn.cursor()

    hashed_password = pwd_context.hash(org.password)

    cursor.execute(
        """
        INSERT INTO organizations
        (organization_name, login_email, password)
        VALUES (%s, %s, %s)
        """,
        (
            org.organization_name,
            org.login_email,
            hashed_password
        )
    )

    conn.commit()

    return {"message": "Organization created successfully!"}


@app.get("/users/")
def get_users():

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, username, email, role
        FROM users
        """
    )

    users = cursor.fetchall()

    return users


@app.get("/organizations/")
def get_organizations():

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, organization_name, login_email
        FROM organizations
        """
    )

    organizations = cursor.fetchall()

    return organizations

@app.post("/login")
def login(user: LoginRequest):

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT email, password, role
            FROM users
            WHERE email = %s
            """,
            (user.email,)
        )

        db_user = cursor.fetchone()

        if db_user is None:
            return {"message": "User not found"}

        if not pwd_context.verify(
            user.password,
            db_user[1]
        ):
            return {"message": "Invalid password"}

        token = create_access_token(
            {
                "sub": db_user[0],
                "role": db_user[2]
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer"
        }

    except Exception as e:
        return {"error": str(e)}
    
@app.post("/send-email")
def send_email(email: EmailRequest):

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO email_logs
            (receiver_email, subject, message)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (
                email.receiver_email,
                email.subject,
                email.message
            )
        )

        email_id = cursor.fetchone()[0]

        conn.commit()

        tracking_url = f"http://127.0.0.1:8000/track/{email_id}"

        html_body = f"""
        <html>
        <body>

        <p>{email.message}</p>

        <img src="{tracking_url}"
             width="1"
             height="1"
             alt="tracking">

        </body>
        </html>
        """

        sender_email = os.getenv("sender_email")
        app_password = os.getenv("app_password")

        msg = MIMEText(html_body, "html")

        msg["From"] = sender_email
        msg["To"] = email.receiver_email
        msg["Subject"] = email.subject

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        server.starttls()

        server.login(
            sender_email,
            app_password
        )

        server.sendmail(
            sender_email,
            email.receiver_email,
            msg.as_string()
        )

        server.quit()

        return {
            "message": "Email Sent Successfully",
            "email_id": email_id
        }

    except Exception as e:

        conn.rollback()

        return {
            "error": str(e)
        }
        
@app.get("/track/{email_id}")
def track_email(email_id: str):

    try:

        conn.rollback()

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE email_logs
            SET status = %s,
                opened_at = NOW()
            WHERE id = %s
            """,
            ("SEEN", email_id)
        )

        conn.commit()

        return {
            "message": "Tracked Successfully",
            "email_id": email_id
        }

    except Exception as e:

        conn.rollback()

        return {
            "error": str(e)
        }
    