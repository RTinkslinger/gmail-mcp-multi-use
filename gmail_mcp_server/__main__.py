"""Entry point for running the package as a module.

Usage:
    python -m gmail_mcp_server serve
    python -m gmail_mcp_server health
"""

from gmail_mcp_server.cli import main

if __name__ == "__main__":
    main()
