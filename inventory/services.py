import smtplib
from django.conf import settings
from django.core.mail import send_mail
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .models import EmailSettings, EmailLog
import random
from datetime import timedelta

from django.utils import timezone

from .models import (
    SetupOTP,
)

def send_email(
    recipient,
    subject,
    message
):

    config = EmailSettings.objects.filter(
        is_active=True
    ).first()

    if not config:

        return (
            False,
            "No active email configuration found."
        )

    try:

        email = MIMEMultipart()

        email["From"] = (
            f"{config.sender_name} <{config.sender_email}>"
        )

        email["To"] = recipient

        email["Subject"] = subject

        email.attach(
            MIMEText(
                message,
                "plain"
            )
        )

        if config.use_ssl:

            server = smtplib.SMTP_SSL(
                config.smtp_host,
                config.smtp_port
            )

        else:

            server = smtplib.SMTP(
                config.smtp_host,
                config.smtp_port
            )

            if config.use_tls:

                server.starttls()

        server.login(

            config.username,

            config.password

        )

        server.sendmail(

            config.sender_email,

            recipient,

            email.as_string()

        )

        server.quit()

        EmailLog.objects.create(

            recipient=recipient,

            subject=subject,

            status="SUCCESS",
            error=""

        )

        return (

            True,

            "Email sent successfully."

        )

    except Exception as e:

        EmailLog.objects.create(

            recipient=recipient,

            subject=subject,

            status="FAILED",

            error=str(e)

        )

        return (

            False,

            str(e)

        )
class InstallationService:

    @staticmethod
    def send_setup_otp(email):

        otp = SetupOTP.generate()

        SetupOTP.objects.filter(
            email=email
        ).delete()

        SetupOTP.objects.create(

            email=email,

            otp=otp,

            expires_at=timezone.now() + timedelta(minutes=5)

        )

        send_mail(

            subject="Medical Shop ERP Installation OTP",

            message=f"""

Your OTP is

{otp}

Valid for 5 minutes.

""",

            from_email=settings.DEFAULT_FROM_EMAIL,

            recipient_list=[email],

            fail_silently=False,

        )

        return True