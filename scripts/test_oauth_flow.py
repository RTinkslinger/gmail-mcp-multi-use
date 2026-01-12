#!/usr/bin/env python3
"""Test script for end-to-end OAuth flow.

This script tests the complete OAuth flow:
1. Loads config from gmail_config.yaml
2. Initializes SQLite storage
3. Creates OAuth manager
4. Runs local OAuth server
5. Opens browser for authentication
6. Handles callback and stores tokens

Usage:
    cd /path/to/gmail-multi-user-dev-mcp/Basic
    python scripts/test_oauth_flow.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gmail_multi_user import ConfigLoader
from gmail_multi_user.oauth import LocalOAuthServer, OAuthManager
from gmail_multi_user.storage import StorageFactory
from gmail_multi_user.tokens import TokenEncryption


async def main() -> int:
    """Run the OAuth test flow."""
    print("=" * 60)
    print("Gmail Multi-User OAuth Test")
    print("=" * 60)
    print()

    # Load configuration
    print("[1/5] Loading configuration...")
    try:
        config = ConfigLoader.load()
        print(f"      Client ID: {config.google.client_id[:20]}...")
        print(f"      Scopes: {config.google.scopes}")
        print(f"      Storage: {config.storage.type}")
        print()
    except Exception as e:
        print(f"      ERROR: Failed to load config: {e}")
        return 1

    # Initialize storage
    print("[2/5] Initializing storage...")
    try:
        storage = StorageFactory.create(config)
        await storage.initialize()
        print(f"      SQLite database ready: {config.storage.sqlite.path}")
        print()
    except Exception as e:
        print(f"      ERROR: Failed to initialize storage: {e}")
        return 1

    # Initialize encryption
    print("[3/5] Initializing encryption...")
    try:
        encryption = TokenEncryption(config.encryption_key)
        if encryption.validate_key():
            print("      Encryption key validated")
            print()
        else:
            print("      ERROR: Invalid encryption key")
            return 1
    except Exception as e:
        print(f"      ERROR: Failed to initialize encryption: {e}")
        return 1

    # Create OAuth manager
    print("[4/5] Creating OAuth manager...")
    try:
        oauth_manager = OAuthManager(config, storage, encryption)
        print("      OAuth manager ready")
        print()
    except Exception as e:
        print(f"      ERROR: Failed to create OAuth manager: {e}")
        return 1

    # Run local OAuth flow
    print("[5/5] Starting OAuth flow...")
    print()
    print("-" * 60)
    print("A browser window should open. Please authenticate with your")
    print("Google account (hi@aacash.me) and grant the requested permissions.")
    print("-" * 60)
    print()

    try:
        local_server = LocalOAuthServer(oauth_manager)
        result = await local_server.run_oauth_flow(
            user_id="test_user_001",
            open_browser=True,
        )

        print()
        print("=" * 60)
        if result.success:
            print("SUCCESS!")
            print(f"  Connection ID: {result.connection_id}")
            print(f"  Gmail Address: {result.gmail_address}")
            print()
            print("The OAuth flow completed successfully. Tokens have been")
            print("encrypted and stored in the database.")
        else:
            print("FAILED")
            print(f"  Error: {result.error}")
            return 1
        print("=" * 60)

    except Exception as e:
        print(f"ERROR: OAuth flow failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Cleanup
        await oauth_manager.close()
        await storage.close()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
