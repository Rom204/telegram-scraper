import argparse
import json
import os

from telethon import events
from telethon.sync import TelegramClient

from client import PHONE_NUMBER, build_client
from groups import load_groups

DATA_DIR = "data"


def get_sender_name(sender):
    if sender is None:
        return None
    # Channels and anonymous group admins have a `title` instead of first/last name
    name = getattr(sender, "title", None)
    if name:
        return name
    first = getattr(sender, "first_name", None)
    last = getattr(sender, "last_name", None)
    name = " ".join(part for part in (first, last) if part)
    return name or None


def build_link(message, group_cfg):
    try:
        entity = group_cfg.entity
        username = getattr(entity, "username", None)
        if username:
            return f"https://t.me/{username}/{message.id}"
        # Private supergroups/channels have no public username.
        # Their Telethon id has a -100 prefix; stripping it gives the
        # internal id that t.me/c/ expects.
        chat_id = str(entity.id)
        if chat_id.startswith("-100"):
            return f"https://t.me/c/{chat_id[4:]}/{message.id}"
        return None
    except Exception:
        return None


def message_to_record(message, group_cfg):
    sender = message.sender
    reply_to_msg_id = getattr(message, "reply_to_msg_id", None)
    return {
        "schema_version": 1,
        "message_id": message.id,
        "group_id": group_cfg.entity.id,
        "group_label": group_cfg.label,
        "sender_id": message.sender_id,
        "sender_username": getattr(sender, "username", None),
        "sender_name": get_sender_name(sender),
        "date": message.date.isoformat(),  # UTC datetime, already timezone-aware from Telethon
        "text": message.text or "",
        "is_reply": reply_to_msg_id is not None,
        "reply_to_msg_id": reply_to_msg_id,
        "link": build_link(message, group_cfg),
    }


def open_writers(groups, data_dir):
    os.makedirs(data_dir, exist_ok=True)
    # Open in append mode so restarting the listener never overwrites existing records
    return {g.label: open(os.path.join(data_dir, f"{g.label}.jsonl"), "a", encoding="utf-8") for g in groups}


def write_record(fh, record):
    # ensure_ascii=False keeps non-Latin text (Hebrew, Arabic, etc.) readable in the file
    fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    # flush() empties Python's buffer; fsync() tells the OS to commit to disk.
    # Both are needed so a crash doesn't lose the last message in the buffer.
    fh.flush()
    os.fsync(fh.fileno())


def backfill(client, group_cfg, writer, limit):
    # iter_messages returns newest-first, so backfilled records will appear
    # in reverse-chronological order at the top of the file. Consumers should
    # sort by message_id or date rather than assuming file order.
    for message in client.iter_messages(group_cfg.entity, limit=limit):
        write_record(writer, message_to_record(message, group_cfg))


def main():
    parser = argparse.ArgumentParser(
        description="Listen for new messages across configured Telegram groups and append them to per-group JSONL files."
    )
    parser.add_argument(
        "--backfill",
        type=int,
        default=0,
        metavar="N",
        help="On startup, fetch the last N messages per group before listening live (default: 0, disabled)",
    )
    parser.add_argument("--data-dir", default=DATA_DIR)
    args = parser.parse_args()

    groups = load_groups()

    with build_client(TelegramClient) as client:
        client.start(phone=PHONE_NUMBER)

        # Resolve group ids/usernames to Telethon entity objects once at startup.
        # Passing resolved entities (not raw strings) to events.NewMessage ensures
        # reliable chat_id matching regardless of whether the config used a numeric
        # id or a @username.
        for g in groups:
            g.entity = client.get_entity(g.group)

        writers = open_writers(groups, args.data_dir)

        # event.chat_id is Telethon's normalized signed integer, which matches
        # entity.id when both come from the same Telethon session — safe as a key.
        group_by_chat_id = {g.entity.id: g for g in groups}

        if args.backfill:
            for g in groups:
                print(f"Backfilling last {args.backfill} message(s) for '{g.label}'...")
                backfill(client, g, writers[g.label], args.backfill)

        chat_entities = [g.entity for g in groups]

        @client.on(events.NewMessage(chats=chat_entities))
        def handler(event):
            group_cfg = group_by_chat_id.get(event.chat_id)
            if group_cfg is None:
                return
            record = message_to_record(event.message, group_cfg)
            write_record(writers[group_cfg.label], record)
            preview = record["text"][:60]
            print(f"[{group_cfg.label}] {record['sender_name']}: {preview}")

        print(f"Listening on {len(groups)} group(s): {[g.label for g in groups]}")
        # Blocks here until disconnected (Ctrl+C, network drop, or session revoked).
        # To run in the background: nohup python3 listener.py &
        client.run_until_disconnected()


if __name__ == "__main__":
    main()
