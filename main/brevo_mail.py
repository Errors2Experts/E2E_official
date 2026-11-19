import base64
import mimetypes
import os
from pathlib import Path

import requests

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


def send_brevo_email(
    to_email,
    subject,
    html_content,
    text_content=None,
    attachment_path=None,
):
    api_key = os.getenv("BREVO_API_KEY")

    if not api_key:
        raise RuntimeError("BREVO_API_KEY environment variable is required.")

    sender_name = os.getenv(
        "BREVO_SENDER_NAME",
    )
    sender_email = os.getenv(
        "BREVO_SENDER_EMAIL",
    )

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json",
    }

    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email,
        },
        "to": [
            {
                "email": to_email,
            }
        ],
        "subject": subject,
        "htmlContent": html_content,
    }

    if text_content:
        payload["textContent"] = text_content

    if attachment_path:
        file_path = Path(attachment_path)

        if file_path.is_file():
            with file_path.open("rb") as attachment_file:
                encoded_content = base64.b64encode(attachment_file.read()).decode(
                    "utf-8"
                )

            mime_type = mimetypes.guess_type(file_path.name)[0]

            payload["attachment"] = [
                {
                    "content": encoded_content,
                    "name": file_path.name,
                    "type": (mime_type or "application/octet-stream"),
                }
            ]

    response = requests.post(
        BREVO_URL,
        json=payload,
        headers=headers,
        timeout=20,
    )

    response.raise_for_status()

    if response.content:
        return response.json()

    return None
