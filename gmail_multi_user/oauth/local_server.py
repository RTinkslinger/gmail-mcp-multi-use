"""Local OAuth callback server for CLI mode.

This module provides a temporary HTTP server that catches the OAuth
callback when running in CLI/MCP mode, enabling a seamless authentication
flow without requiring manual URL/code copying.
"""

from __future__ import annotations

import asyncio
import socket
import webbrowser
from dataclasses import dataclass
from typing import TYPE_CHECKING

from gmail_multi_user.types import CallbackResult

if TYPE_CHECKING:
    from gmail_multi_user.oauth.manager import OAuthManager


@dataclass
class LocalOAuthResult:
    """Result from local OAuth flow."""

    success: bool
    connection_id: str | None = None
    gmail_address: str | None = None
    error: str | None = None


class LocalOAuthServer:
    """Local HTTP server for OAuth callback handling.

    This server:
    1. Finds an available port
    2. Starts a temporary HTTP server
    3. Opens the browser to the authorization URL
    4. Waits for the OAuth callback
    5. Processes the callback and returns the result

    Example:
        server = LocalOAuthServer(oauth_manager)
        result = await server.run_oauth_flow(user_id="user_123")
        if result.success:
            print(f"Connected: {result.gmail_address}")
    """

    DEFAULT_PORT_RANGE = (8000, 9000)
    DEFAULT_TIMEOUT = 300  # 5 minutes

    def __init__(
        self,
        oauth_manager: OAuthManager,
        port_range: tuple[int, int] = DEFAULT_PORT_RANGE,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the local OAuth server.

        Args:
            oauth_manager: OAuth manager for handling the flow.
            port_range: Range of ports to try (start, end).
            timeout: Timeout in seconds for waiting for callback.
        """
        self._oauth_manager = oauth_manager
        self._port_range = port_range
        self._timeout = timeout
        self._callback_result: CallbackResult | None = None
        self._callback_event: asyncio.Event | None = None

    async def run_oauth_flow(
        self,
        user_id: str,
        scopes: list[str] | None = None,
        open_browser: bool = True,
    ) -> LocalOAuthResult:
        """Run the complete OAuth flow with local callback server.

        Args:
            user_id: External user identifier.
            scopes: OAuth scopes to request.
            open_browser: Whether to automatically open browser.

        Returns:
            LocalOAuthResult with connection details or error.
        """
        # Find available port
        port = self._find_available_port()
        if port is None:
            return LocalOAuthResult(
                success=False,
                error=f"No available port in range {self._port_range}",
            )

        redirect_uri = f"http://localhost:{port}/oauth/callback"

        # Get authorization URL
        auth_result = await self._oauth_manager.get_auth_url(
            user_id=user_id,
            scopes=scopes,
            redirect_uri=redirect_uri,
        )

        # Reset callback state
        self._callback_result = None
        self._callback_event = asyncio.Event()

        # Start server
        try:
            import uvicorn

            app = self._create_app()  # type: ignore[no-untyped-call]

            # Create server config
            config = uvicorn.Config(
                app,
                host="127.0.0.1",
                port=port,
                log_level="warning",
            )
            server = uvicorn.Server(config)

            # Start server in background
            server_task = asyncio.create_task(server.serve())

            # Wait for server to start
            await asyncio.sleep(0.5)

            # Open browser or print URL
            if open_browser:
                print("\nOpening browser for authentication...")
                print(f"If browser doesn't open, visit:\n{auth_result.auth_url}\n")
                webbrowser.open(auth_result.auth_url)
            else:
                print(
                    f"\nPlease visit this URL to authenticate:\n{auth_result.auth_url}\n"
                )

            # Wait for callback with timeout
            try:
                await asyncio.wait_for(
                    self._callback_event.wait(),
                    timeout=self._timeout,
                )
            except asyncio.TimeoutError:
                return LocalOAuthResult(
                    success=False,
                    error=f"Authentication timed out after {self._timeout} seconds",
                )

            # Shutdown server
            server.should_exit = True
            await server_task

            # Return result
            if self._callback_result and self._callback_result.success:
                return LocalOAuthResult(
                    success=True,
                    connection_id=self._callback_result.connection_id,
                    gmail_address=self._callback_result.gmail_address,
                )
            else:
                return LocalOAuthResult(
                    success=False,
                    error=self._callback_result.error
                    if self._callback_result
                    else "Unknown error",
                )

        except ImportError:
            return LocalOAuthResult(
                success=False,
                error="starlette and uvicorn are required for local OAuth server",
            )
        except Exception as e:
            return LocalOAuthResult(
                success=False,
                error=str(e),
            )

    def _create_app(self):  # type: ignore[no-untyped-def]
        """Create the Starlette application for handling callbacks."""
        from starlette.applications import Starlette
        from starlette.responses import HTMLResponse
        from starlette.routing import Route

        async def handle_callback(request):  # type: ignore[no-untyped-def]
            """Handle the OAuth callback."""
            code = request.query_params.get("code")
            state = request.query_params.get("state")
            error = request.query_params.get("error")

            if error:
                self._callback_result = CallbackResult(
                    success=False,
                    error=f"OAuth error: {error}",
                )
                html = self._render_error_page(error)
            elif code and state:
                # Process the callback
                self._callback_result = await self._oauth_manager.handle_callback(
                    code=code,
                    state=state,
                )

                if self._callback_result.success:
                    html = self._render_success_page(
                        self._callback_result.gmail_address or "Unknown"
                    )
                else:
                    html = self._render_error_page(
                        self._callback_result.error or "Unknown error"
                    )
            else:
                self._callback_result = CallbackResult(
                    success=False,
                    error="Missing code or state parameter",
                )
                html = self._render_error_page("Missing authorization code")

            # Signal that callback was received
            if self._callback_event:
                self._callback_event.set()

            return HTMLResponse(html)

        routes = [
            Route("/oauth/callback", handle_callback),
        ]

        return Starlette(routes=routes)

    def _find_available_port(self) -> int | None:
        """Find an available port in the configured range.

        Returns:
            Available port number, or None if no port available.
        """
        start, end = self._port_range

        for port in range(start, end + 1):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("127.0.0.1", port))
                    return port
            except OSError:
                continue

        return None

    @staticmethod
    def _render_success_page(gmail_address: str) -> str:
        """Render the success HTML page."""
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Gmail Connected</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            padding: 3rem;
            border-radius: 1rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
            max-width: 400px;
        }}
        .icon {{
            font-size: 4rem;
            margin-bottom: 1rem;
        }}
        h1 {{
            color: #1a1a1a;
            margin: 0 0 0.5rem 0;
        }}
        .email {{
            color: #4a5568;
            font-size: 1.1rem;
            margin-bottom: 1.5rem;
        }}
        .message {{
            color: #718096;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">✓</div>
        <h1>Gmail Connected!</h1>
        <p class="email">{gmail_address}</p>
        <p class="message">You can close this window and return to your application.</p>
    </div>
</body>
</html>"""

    @staticmethod
    def _render_error_page(error: str) -> str:
        """Render the error HTML page."""
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Connection Failed</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
        }}
        .container {{
            background: white;
            padding: 3rem;
            border-radius: 1rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
            max-width: 400px;
        }}
        .icon {{
            font-size: 4rem;
            margin-bottom: 1rem;
        }}
        h1 {{
            color: #1a1a1a;
            margin: 0 0 0.5rem 0;
        }}
        .error {{
            color: #e53e3e;
            font-size: 0.95rem;
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: #fff5f5;
            border-radius: 0.5rem;
        }}
        .message {{
            color: #718096;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">✗</div>
        <h1>Connection Failed</h1>
        <p class="error">{error}</p>
        <p class="message">Please close this window and try again.</p>
    </div>
</body>
</html>"""
