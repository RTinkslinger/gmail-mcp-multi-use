# Phase 2: OAuth & Token Management

**Duration:** Week 2
**Dependencies:** Phase 1 (Foundation)

---

## Objectives

1. Implement OAuth 2.0 authorization flow with PKCE
2. Build token exchange and storage
3. Create token refresh mechanism
4. Implement local OAuth server for CLI mode

---

## Deliverables

- [ ] Complete OAuth flow (URL → callback → tokens)
- [ ] PKCE implementation
- [ ] Token encryption and storage
- [ ] Automatic token refresh
- [ ] Local OAuth callback server
- [ ] Tests for all OAuth flows

---

## Task Breakdown

### 2.1 OAuth State Management

```
□ Create gmail_multi_user/oauth/state.py
  □ OAuthStateManager class
  □ generate_state() - 32-byte random
  □ create_state() - store in DB with TTL
  □ validate_state() - check exists and not expired
  □ consume_state() - delete after use
  □ cleanup_expired() - remove old states
```

**Testing:**
- State generation is cryptographically random
- State expires after 10 minutes
- Consumed state cannot be reused
- Invalid state returns None

### 2.2 PKCE Implementation

```
□ Create gmail_multi_user/oauth/pkce.py
  □ generate_code_verifier() - 64-char random
  □ generate_code_challenge() - SHA256 + base64url
  □ validate_verifier_length() - 43-128 chars
```

**Testing:**
- Verifier meets RFC 7636 requirements
- Challenge correctly computed
- Round-trip validation

### 2.3 OAuth Manager

```
□ Create gmail_multi_user/oauth/manager.py
  □ OAuthManager class
  □ __init__(config, storage)
  □ get_auth_url(user_id, scopes, redirect_uri)
    □ Create/get user
    □ Generate state and PKCE
    □ Store OAuth state
    □ Build Google OAuth URL
    □ Return AuthUrlResult
  □ handle_callback(code, state)
    □ Validate state
    □ Exchange code for tokens
    □ Get user email from Google
    □ Encrypt tokens
    □ Create connection
    □ Delete OAuth state
    □ Return CallbackResult
  □ _build_auth_url() helper
  □ _exchange_code() helper
  □ _get_user_email() helper
```

**Testing:**
- Auth URL contains all required params
- Callback validates state
- Invalid state returns error
- Token exchange calls Google correctly
- Tokens encrypted before storage

### 2.4 Token Manager

```
□ Create gmail_multi_user/tokens/manager.py
  □ TokenManager class
  □ __init__(config, storage)
  □ get_valid_token(connection)
    □ Decrypt access token
    □ Check expiration (5-min buffer)
    □ Refresh if needed
    □ Return valid token
  □ refresh_token(connection)
    □ Decrypt refresh token
    □ Call Google refresh endpoint
    □ Encrypt new access token
    □ Update connection in storage
  □ mark_needs_reauth(connection)
    □ Set is_active = False
    □ Set needs_reauth = True
```

**Testing:**
- Valid token returned without refresh
- Expiring token triggers refresh
- Expired token triggers refresh
- Refresh failure marks needs_reauth
- Tokens correctly encrypted/decrypted

### 2.5 Google OAuth Client

```
□ Create gmail_multi_user/oauth/google.py
  □ GoogleOAuthClient class
  □ exchange_code(code, code_verifier, redirect_uri)
    □ POST to token endpoint
    □ Parse response
    □ Return tokens + expiry
  □ refresh_access_token(refresh_token)
    □ POST to token endpoint
    □ Parse response
    □ Return new access token + expiry
  □ get_user_info(access_token)
    □ GET userinfo endpoint
    □ Return email address
  □ revoke_token(token)
    □ POST to revoke endpoint
```

**Testing:**
- Exchange returns tokens (mocked)
- Refresh returns new token (mocked)
- Network errors handled
- Invalid response handled

### 2.6 Local OAuth Server

```
□ Create gmail_multi_user/oauth/local_server.py
  □ LocalOAuthServer class
  □ run_oauth_flow(user_id)
    □ Find available port (8000-9000)
    □ Start async HTTP server
    □ Open browser to auth URL
    □ Wait for callback (5-min timeout)
    □ Process callback
    □ Stop server
    □ Return result
  □ _start_server(port) - Starlette app
  □ _handle_callback(request) - extract code/state
  □ _find_available_port()
□ Create templates/oauth_success.html
□ Create templates/oauth_error.html
```

**Testing:**
- Server starts on available port
- Callback received and processed
- Success page rendered
- Timeout handled gracefully

### 2.7 OAuth HTTP Routes

```
□ Create gmail_multi_user/oauth/routes.py
  □ OAuth routes for HTTP mode
  □ GET /oauth/start - redirect to Google
  □ GET /oauth/callback - handle callback
  □ Mount on Starlette app
```

**Testing:**
- Routes respond correctly
- Callback processes successfully
- Errors render error page

### 2.8 Integration

```
□ Wire OAuth into GmailService
  □ get_auth_url() method
  □ handle_oauth_callback() method
  □ Token refresh in get_connection()
□ Create tests/unit/test_oauth.py
□ Create tests/unit/test_tokens.py
□ Create tests/integration/test_oauth_flow.py
```

**Testing:**
- Full OAuth flow works end-to-end (mocked Google)
- Token refresh works end-to-end

---

## Definition of Done

- [ ] All tasks checked off
- [ ] OAuth URL generation works
- [ ] Callback processing works
- [ ] Token refresh works
- [ ] Local OAuth server works
- [ ] All tests pass with 90%+ coverage
- [ ] No hardcoded secrets

---

## Risks

| Risk | Mitigation |
|------|------------|
| Google OAuth changes | Use official libraries, test against real Google |
| Port conflicts for local server | Dynamic port finding, fallback ports |
| Browser not opening | Print URL as fallback |
