import requests
from django.conf import settings


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

    try:

        response = requests.post(
            

            "https://api.brevo.com/v3/smtp/email",

            headers={

                "accept":"application/json",

                "api-key":settings.BREVO_API_KEY,

                "content-type":"application/json"

            },

            json={
"sender": {
    "name": settings.DEFAULT_FROM_NAME,
    "email": settings.DEFAULT_FROM_EMAIL
},

                "to":[

                    {

                        "email":recipient

                    }

                ],

                "subject":subject,

                "textContent":message

            },

            timeout=15

        )
        print("STATUS:", response.status_code)
        print("BODY:", response.text)
        if response.status_code not in (200, 201):
            raise Exception(f"Brevo {response.status_code}: {response.text}")

        EmailLog.objects.create(

            recipient=recipient,

            subject=subject,

            status="SUCCESS",

            error=""

        )

        return (

            True,

            "Email Sent Successfully"

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

            expires_at=timezone.now()+timedelta(minutes=5)

        )

        success,msg=send_email(

            recipient=email,

            subject="Medical Shop ERP Installation OTP",

            message=f"""

Your OTP is

{otp}

Valid for 5 minutes.

"""

        )

        if not success:

            raise Exception(msg)

        return True