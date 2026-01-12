#!/usr/bin/env python3
"""End-to-end test script for Gmail write operations.

This script tests the Gmail write functionality with a real account:
- Creating drafts
- Updating drafts
- Modifying labels
- Deleting drafts

NOTE: This script does NOT send real emails to avoid spam.
It only tests draft operations which are safe.

Prerequisites:
1. Run scripts/test_oauth_flow.py first to authenticate
2. Ensure gmail_config.yaml has valid credentials
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gmail_multi_user.config import Config, ConfigLoader
from gmail_multi_user.service import GmailService
from gmail_multi_user.storage.sqlite import SQLiteBackend
from gmail_multi_user.tokens.encryption import TokenEncryption
from gmail_multi_user.tokens.manager import TokenManager


async def main() -> None:
    """Run Gmail write tests."""
    print("=" * 60)
    print("Gmail Write Operations Test")
    print("=" * 60)

    # Load config
    loader = ConfigLoader()
    config = loader.load()
    print(f"\nConfig loaded from: {loader.get_config_path()}")

    # Initialize storage
    storage = SQLiteBackend(config.storage.sqlite.path)
    await storage.initialize()
    print(f"Storage initialized: {config.storage.sqlite.path}")

    # Initialize encryption
    encryption = TokenEncryption(config.encryption_key)

    # Initialize token manager
    token_manager = TokenManager(config, storage, encryption)

    # Initialize service
    service = GmailService(config, storage, token_manager)

    try:
        # Get the first active connection
        connections = await storage.list_connections()
        if not connections:
            print("\nERROR: No connections found. Run test_oauth_flow.py first.")
            return

        connection = connections[0]
        connection_id = connection.id
        print(f"\nUsing connection: {connection.gmail_address}")
        print(f"Connection ID: {connection_id}")

        # Test 1: Get profile to verify connection
        print("\n" + "-" * 40)
        print("Test 1: Verify connection with profile")
        print("-" * 40)
        profile = await service.get_profile(connection_id)
        print(f"Email: {profile['email_address']}")
        print(f"Messages: {profile['messages_total']}")

        # Test 2: Create a draft
        print("\n" + "-" * 40)
        print("Test 2: Create a draft")
        print("-" * 40)
        draft_result = await service.create_draft(
            connection_id=connection_id,
            to=["test@example.com"],
            subject="Test Draft from Gmail MCP",
            body="This is a test draft created by the Gmail MCP library.\n\nThis draft will be deleted after testing.",
            body_html="<h1>Test Draft</h1><p>This is a test draft created by the Gmail MCP library.</p>",
        )
        print(f"Draft created!")
        print(f"  Draft ID: {draft_result.draft_id}")
        print(f"  Message ID: {draft_result.message_id}")

        draft_id = draft_result.draft_id

        # Test 3: Update the draft
        print("\n" + "-" * 40)
        print("Test 3: Update the draft")
        print("-" * 40)
        updated_draft = await service.update_draft(
            connection_id=connection_id,
            draft_id=draft_id,
            to=["updated@example.com"],
            subject="Updated Test Draft from Gmail MCP",
            body="This draft has been updated!\n\nThe recipient and subject were changed.",
        )
        print(f"Draft updated!")
        print(f"  Draft ID: {updated_draft.draft_id}")

        # Test 4: Search for messages and test label operations
        print("\n" + "-" * 40)
        print("Test 4: Search and test label operations")
        print("-" * 40)
        search_result = await service.search(
            connection_id=connection_id,
            query="is:inbox",
            max_results=1,
            include_body=False,
        )

        if search_result.messages:
            msg = search_result.messages[0]
            print(f"Found message: {msg.subject[:50]}...")
            print(f"  Message ID: {msg.id}")
            print(f"  Labels: {msg.labels}")

            # Test marking as unread then read (non-destructive)
            print("\n  Testing mark_unread...")
            await service.mark_unread(connection_id, [msg.id])
            print("  Marked as unread")

            print("  Testing mark_read...")
            await service.mark_read(connection_id, [msg.id])
            print("  Marked as read")
        else:
            print("No messages found in inbox to test label operations")

        # Test 5: Delete the draft (cleanup)
        print("\n" + "-" * 40)
        print("Test 5: Delete the draft (cleanup)")
        print("-" * 40)
        await service.delete_draft(connection_id=connection_id, draft_id=draft_id)
        print(f"Draft deleted: {draft_id}")

        print("\n" + "=" * 60)
        print("All tests passed!")
        print("=" * 60)

    finally:
        await service.close()
        await storage.close()


if __name__ == "__main__":
    asyncio.run(main())
