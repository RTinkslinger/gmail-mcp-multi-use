"""OAuth 2.0 implementation for gmail-multi-user-mcp.

This package provides OAuth flow handling with PKCE support.
"""

from gmail_multi_user.oauth.google import GoogleOAuthClient, TokenResponse, UserInfo
from gmail_multi_user.oauth.local_server import LocalOAuthResult, LocalOAuthServer
from gmail_multi_user.oauth.manager import OAuthManager
from gmail_multi_user.oauth.pkce import PKCE
from gmail_multi_user.oauth.state import OAuthStateManager

__all__ = [
    "GoogleOAuthClient",
    "LocalOAuthResult",
    "LocalOAuthServer",
    "OAuthManager",
    "OAuthStateManager",
    "PKCE",
    "TokenResponse",
    "UserInfo",
]
