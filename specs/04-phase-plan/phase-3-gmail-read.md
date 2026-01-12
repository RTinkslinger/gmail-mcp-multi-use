# Phase 3: Gmail Read Operations

**Duration:** Week 3
**Dependencies:** Phase 2 (OAuth)

---

## Objectives

1. Implement Gmail API client
2. Build message search functionality
3. Implement message and thread retrieval
4. Create MIME parsing utilities
5. Add attachment handling

---

## Deliverables

- [ ] Gmail API wrapper for read operations
- [ ] Search with Gmail query syntax
- [ ] Full message retrieval with parsing
- [ ] Thread retrieval
- [ ] Attachment download
- [ ] Label listing
- [ ] Tests with mocked Gmail API

---

## Task Breakdown

### 3.1 Gmail API Client Setup

```
□ Create gmail_multi_user/gmail/client.py
  □ GmailAPIClient class
  □ __init__() - initialize httpx client
  □ _make_request(method, endpoint, token, params, body)
    □ Build full URL
    □ Add Authorization header
    □ Handle rate limits (429)
    □ Handle errors
    □ Return JSON response
  □ _handle_gmail_error(response)
    □ Parse error response
    □ Raise appropriate exception
```

**Testing:**
- Requests include auth header
- Rate limits trigger RateLimitError
- API errors trigger GmailAPIError

### 3.2 Message Search

```
□ Add to gmail/client.py:
  □ search(token, query, max_results, page_token)
    □ GET /messages with q parameter
    □ Parse message list
    □ Return message IDs + estimate
  □ Support Gmail query syntax
□ Create gmail_multi_user/gmail/messages.py
  □ Message dataclass enhancements
  □ Parse message list response
```

**Testing:**
- Search returns message IDs
- Pagination works
- Empty results handled
- Query passed correctly

### 3.3 Message Retrieval

```
□ Add to gmail/client.py:
  □ get_message(token, message_id, format)
    □ GET /messages/{id}
    □ Support full/metadata/minimal format
    □ Parse response into Message
  □ batch_get_messages(token, message_ids, format)
    □ Batch API request
    □ Parse multiple responses
```

**Testing:**
- Full message retrieved
- Metadata only works
- Batch request efficient
- Not found handled

### 3.4 MIME Parsing

```
□ Create gmail_multi_user/gmail/parser.py
  □ MIMEParser class
  □ parse_message(raw_payload)
    □ Extract headers
    □ Find text/plain body
    □ Find text/html body
    □ List attachments
  □ _parse_part(part) - recursive part parsing
  □ _decode_body(data, encoding) - base64 decode
  □ _parse_headers(headers) - header dict
  □ _parse_address(header) - name + email
```

**Testing:**
- Simple text message parsed
- HTML message parsed
- Multipart message parsed
- Nested MIME handled
- Attachments listed

### 3.5 Thread Retrieval

```
□ Add to gmail/client.py:
  □ get_thread(token, thread_id)
    □ GET /threads/{id}
    □ Parse all messages in thread
    □ Return Thread with messages
```

**Testing:**
- Thread with multiple messages
- Single message thread
- Thread metadata correct

### 3.6 Label Operations

```
□ Create gmail_multi_user/gmail/labels.py
  □ Label dataclass
  □ list_labels(token) - GET /labels
  □ Parse label response
□ Add to gmail/client.py:
  □ list_labels(token)
```

**Testing:**
- System labels returned
- User labels returned
- Label counts included

### 3.7 Attachment Handling

```
□ Create gmail_multi_user/gmail/attachments.py
  □ Attachment dataclass
  □ AttachmentData dataclass
□ Add to gmail/client.py:
  □ get_attachment(token, message_id, attachment_id)
    □ GET /messages/{mid}/attachments/{aid}
    □ Decode base64 data
    □ Return AttachmentData
```

**Testing:**
- Attachment retrieved
- Base64 decoded correctly
- Large attachment handled
- Not found handled

### 3.8 Service Integration

```
□ Update gmail_multi_user/service.py:
  □ search(connection_id, query, ...)
    □ Get connection
    □ Get valid token
    □ Call Gmail API
    □ Update last_used_at
  □ get_message(connection_id, message_id, ...)
  □ get_thread(connection_id, thread_id)
  □ list_labels(connection_id)
  □ get_attachment(connection_id, message_id, attachment_id)
```

**Testing:**
- Service correctly delegates to API
- Token validation happens
- Connection updated on use

### 3.9 Client Integration

```
□ Update gmail_multi_user/client.py:
  □ Add all read methods to GmailClient
  □ Add all read methods to AsyncGmailClient
□ Create tests/unit/test_gmail_api.py
□ Create tests/unit/test_parser.py
□ Create tests/mocks/gmail_api.py - mock responses
```

**Testing:**
- Sync client works
- Async client works
- Mocked responses realistic

---

## Definition of Done

- [ ] All tasks checked off
- [ ] Search works with Gmail queries
- [ ] Full message retrieval works
- [ ] Thread retrieval works
- [ ] Attachments downloadable
- [ ] Labels listed
- [ ] All tests pass with 90%+ coverage

---

## Risks

| Risk | Mitigation |
|------|------------|
| Gmail API response changes | Pin to API v1, test with real responses |
| Large message handling | Implement pagination, streaming |
| MIME edge cases | Test with diverse email samples |
