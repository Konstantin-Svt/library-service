import requests
from django.conf import settings
from requests import Response


def send_telegram(text: str) -> Response:
    response = requests.post(
        url=f"https://api.telegram.org/bot{
        settings.TELEGRAM_BOT_TOKEN
        }/sendMessage",
        json={
            "chat_id": settings.TELEGRAM_CHAT_ID,
            "text": text,
        },
        headers={"Content-Type": "application/json"},
        timeout=5,
    )
    return response
