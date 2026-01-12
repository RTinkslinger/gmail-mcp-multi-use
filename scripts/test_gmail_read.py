#!/usr/bin/env python3
"""Test script for Gmail read operations.

This script tests the Gmail read operations using a real connection:
1. Search for messages
2. Get a message with full content
3. Get a thread
4. List labels
5. Get profile info

Usage:
    cd /path/to/gmail-multi-user-dev-mcp/Basic
    python scripts/test_gmail_read.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gmail_multi_user import ConfigLoader
from gmail_multi_user.service import GmailService
from gmail_multi_user.storage import StorageFactory
from gmail_multi_user.tokens import TokenEncryption
from gmail_multi_user.tokens.manager import TokenManager


async def main() -> int:
    """Run the Gmail read tests."""
    print("=" * 60)
    print("Gmail Read Operations Test")
    print("=" * 60)
    print()

    # Load configuration
    print("[1/6] Loading configuration and initializing...")
    try:
        config = ConfigLoader.load()
        storage = StorageFactory.create(config)
        await storage.initialize()
        encryption = TokenEncryption(config.encryption_key)
        token_manager = TokenManager(config, storage, encryption)
        service = GmailService(config, storage, token_manager)
        print("      Initialized successfully")
        print()
    except Exception as e:
        print(f"      ERROR: {e}")
        return 1

    # Find the existing connection
    print("[2/6] Finding existing connection...")
    try:
        connections = await storage.list_connections()
        if not connections:
            print("      ERROR: No connections found. Run test_oauth_flow.py first.")
            return 1

        connection = connections[0]
        print(f"      Found connection: {connection.gmail_address}")
        print(f"      Connection ID: {connection.id}")
        print()
    except Exception as e:
        print(f"      ERROR: {e}")
        return 1

    # Get profile
    print("[3/6] Getting Gmail profile...")
    try:
        profile = await service.get_profile(connection.id)
        print(f"      Email: {profile['email_address']}")
        print(f"      Total messages: {profile['messages_total']}")
        print(f"      Total threads: {profile['threads_total']}")
        print()
    except Exception as e:
        print(f"      ERROR: {e}")
        import traceback
        traceback.print_exc()

    # List labels
    print("[4/6] Listing labels...")
    try:
        labels = await service.list_labels(connection.id)
        system_labels = [l for l in labels if l.type == "system"]
        user_labels = [l for l in labels if l.type == "user"]
        print(f"      System labels: {len(system_labels)}")
        print(f"      User labels: {len(user_labels)}")
        for label in labels[:5]:
            print(f"        - {label.name} ({label.id})")
        if len(labels) > 5:
            print(f"        ... and {len(labels) - 5} more")
        print()
    except Exception as e:
        print(f"      ERROR: {e}")
        import traceback
        traceback.print_exc()

    # Search for messages
    print("[5/6] Searching for recent messages...")
    try:
        result = await service.search(
            connection_id=connection.id,
            query="in:inbox",
            max_results=5,
            include_body=False,
        )
        print(f"      Found ~{result.total_estimate} messages")
        print(f"      Returned: {len(result.messages)} messages")
        for msg in result.messages:
            print(f"        - {msg.subject[:50]}... from {msg.from_.email}")
        print()
    except Exception as e:
        print(f"      ERROR: {e}")
        import traceback
        traceback.print_exc()

    # Get a full message
    print("[6/6] Getting full message content...")
    if result.messages:
        try:
            msg_id = result.messages[0].id
            full_msg = await service.get_message(
                connection_id=connection.id,
                message_id=msg_id,
                format="full",
            )
            print(f"      Subject: {full_msg.subject}")
            print(f"      From: {full_msg.from_.name} <{full_msg.from_.email}>")
            print(f"      Date: {full_msg.date}")
            print(f"      Labels: {full_msg.labels}")
            print(f"      Has attachments: {full_msg.has_attachments}")
            if full_msg.attachments:
                for att in full_msg.attachments:
                    print(f"        - {att.filename} ({att.mime_type}, {att.size} bytes)")
            body_preview = full_msg.body_plain[:200] if full_msg.body_plain else "(no plain text body)"
            print(f"      Body preview: {body_preview}...")
            print()
        except Exception as e:
            print(f"      ERROR: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("      No messages to fetch")
        print()

    # Cleanup
    await service.close()
    await storage.close()

    print("=" * 60)
    print("Gmail Read Operations Test Complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
