import os

from dotenv import load_dotenv

load_dotenv()

API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
PHONE_NUMBER = os.environ.get("PHONE_NUMBER")

# Telegram's anti-bot system silently withholds login codes unless the
# client spoofs a real-looking device fingerprint. Do not construct
# TelegramClient anywhere else in this codebase without these kwargs.
CLIENT_KWARGS = dict(
    device_model="Samsung SM-G998B",
    system_version="SDK 33",
    app_version="10.5.4",
    lang_code="en",
    system_lang_code="en-US",
)


def build_client(client_cls, session_name="scraper_session"):
    if not API_ID or not API_HASH:
        raise SystemExit("API_ID and API_HASH must be set in .env (see .env.example)")
    return client_cls(session_name, int(API_ID), API_HASH, **CLIENT_KWARGS)
