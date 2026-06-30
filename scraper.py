import argparse
import os
import sys

from dotenv import load_dotenv
from telethon.sync import TelegramClient

load_dotenv()

API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
PHONE_NUMBER = os.environ.get("PHONE_NUMBER")


def parse_group_id(raw: str):
    try:
        return int(raw)
    except ValueError:
        return raw


def main():
    parser = argparse.ArgumentParser(description="Print the last 10 messages from a Telegram group.")
    parser.add_argument("group_id", help="Numeric group ID, @username, or t.me link")
    args = parser.parse_args()

    if not API_ID or not API_HASH:
        sys.exit("API_ID and API_HASH must be set in .env (see .env.example)")

    group = parse_group_id(args.group_id)

    with TelegramClient(
        "scraper_session",
        int(API_ID),
        API_HASH,
        device_model="Samsung SM-G998B",
        system_version="SDK 33",
        app_version="10.5.4",
        lang_code="en",
        system_lang_code="en-US",
    ) as client:
        client.start(phone=PHONE_NUMBER)

        entity = client.get_entity(group)

        for message in client.iter_messages(entity, limit=10):
            sender = message.sender
            sender_name = getattr(sender, "username", None) or getattr(sender, "title", None) or getattr(sender, "first_name", None) or message.sender_id
            text = message.text or "[no text]"
            print(f"[{message.date}] {sender_name}: {text}")


if __name__ == "__main__":
    main()
