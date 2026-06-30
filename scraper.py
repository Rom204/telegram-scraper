import argparse

from telethon.sync import TelegramClient

from client import PHONE_NUMBER, build_client


def parse_group_id(raw: str):
    try:
        return int(raw)
    except ValueError:
        return raw


def main():
    parser = argparse.ArgumentParser(description="Print the last 10 messages from a Telegram group.")
    parser.add_argument("group_id", help="Numeric group ID, @username, or t.me link")
    args = parser.parse_args()

    group = parse_group_id(args.group_id)

    with build_client(TelegramClient) as client:
        client.start(phone=PHONE_NUMBER)

        entity = client.get_entity(group)

        for message in client.iter_messages(entity, limit=10):
            sender = message.sender
            sender_name = getattr(sender, "username", None) or getattr(sender, "title", None) or getattr(sender, "first_name", None) or message.sender_id
            text = message.text or "[no text]"
            print(f"[{message.date}] {sender_name}: {text}")


if __name__ == "__main__":
    main()
