# Phase 4: Gmail Write Operations

**Duration:** Week 4
**Dependencies:** Phase 3 (Gmail Read)

---

## Objectives

1. Implement email sending
2. Build draft operations
3. Add reply/forward threading
4. Implement label management
5. Add archive/trash operations

---

## Deliverables

- [ ] Send email (plain text, HTML)
- [ ] Attachment support
- [ ] Draft CRUD operations
- [ ] Reply threading
- [ ] Label modification
- [ ] Archive and trash
- [ ] Tests for all write operations

---

## Task Breakdown

### 4.1 MIME Message Building

```
□ Create gmail_multi_user/gmail/composer.py
  □ MessageComposer class
  □ compose(to, subject, body, body_html, cc, bcc, attachments)
    □ Build MIME message
    □ Handle plain text
    □ Handle HTML with multipart/alternative
    □ Handle attachments with multipart/mixed
    □ Return base64url encoded raw message
  □ _create_text_part(body)
  □ _create_html_part(body_html)
  □ _create_attachment_part(attachment)
  □ _encode_message(mime_msg) - base64url encode
```

**Testing:**
- Plain text message composed
- HTML message composed
- Multipart message correct
- Attachments attached
- Headers set correctly

### 4.2 Send Email

```
□ Add to gmail/client.py:
  □ send_message(token, raw_message)
    □ POST /messages/send
    □ Body: {"raw": base64_message}
    □ Return message_id, thread_id
```

**Testing:**
- Send succeeds (mocked)
- Response parsed correctly
- Errors handled

### 4.3 Reply Threading

```
□ Update gmail/composer.py:
  □ compose_reply(to, subject, body, original_message)
    □ Set In-Reply-To header
    □ Set References header
    □ Set Subject (Re: prefix)
    □ Build threaded message
  □ _get_reply_headers(original)
```

**Testing:**
- Reply has correct headers
- Thread ID preserved
- Subject prefixed

### 4.4 Draft Operations

```
□ Create gmail_multi_user/gmail/drafts.py
  □ Draft dataclass
  □ DraftResult dataclass
□ Add to gmail/client.py:
  □ create_draft(token, raw_message)
    □ POST /drafts
    □ Return draft_id, message_id
  □ update_draft(token, draft_id, raw_message)
    □ PUT /drafts/{id}
  □ send_draft(token, draft_id)
    □ POST /drafts/{id}/send
    □ Return message_id, thread_id
  □ delete_draft(token, draft_id)
    □ DELETE /drafts/{id}
  □ get_draft(token, draft_id)
    □ GET /drafts/{id}
```

**Testing:**
- Create draft succeeds
- Update draft succeeds
- Send draft succeeds
- Delete draft succeeds
- Not found handled

### 4.5 Label Management

```
□ Add to gmail/client.py:
  □ modify_labels(token, message_id, add_labels, remove_labels)
    □ POST /messages/{id}/modify
    □ Body: {"addLabelIds": [...], "removeLabelIds": [...]}
    □ Return updated label list
  □ batch_modify_labels(token, message_ids, add_labels, remove_labels)
    □ Batch request for multiple messages
```

**Testing:**
- Add label succeeds
- Remove label succeeds
- Batch modify works
- Invalid label handled

### 4.6 Archive/Trash Operations

```
□ Add to gmail/client.py:
  □ archive_message(token, message_id)
    □ Remove INBOX label
  □ trash_message(token, message_id)
    □ POST /messages/{id}/trash
  □ untrash_message(token, message_id)
    □ POST /messages/{id}/untrash
  □ mark_read(token, message_ids)
    □ Remove UNREAD label
  □ mark_unread(token, message_ids)
    □ Add UNREAD label
```

**Testing:**
- Archive removes INBOX
- Trash moves to trash
- Untrash restores
- Read/unread toggle works

### 4.7 Service Integration

```
□ Update gmail_multi_user/service.py:
  □ send(connection_id, to, subject, body, ...)
    □ Compose message
    □ Get valid token
    □ Send via API
  □ create_draft(connection_id, ...)
  □ update_draft(connection_id, draft_id, ...)
  □ send_draft(connection_id, draft_id)
  □ delete_draft(connection_id, draft_id)
  □ modify_labels(connection_id, message_id, ...)
  □ archive(connection_id, message_id)
  □ trash(connection_id, message_id)
  □ untrash(connection_id, message_id)
  □ mark_read(connection_id, message_ids)
  □ mark_unread(connection_id, message_ids)
```

**Testing:**
- All operations delegate correctly
- Token validation happens
- Scope validation enforced

### 4.8 Scope Validation

```
□ Create gmail_multi_user/gmail/scopes.py
  □ SCOPE_REQUIREMENTS dict
  □ validate_scope(operation, connection_scopes)
  □ Raise GmailAPIError if insufficient scope
□ Integrate scope validation into service methods
```

**Testing:**
- Send requires gmail.send or gmail.compose
- Modify requires gmail.modify
- Read-only scope blocks write ops

### 4.9 Client Integration

```
□ Update gmail_multi_user/client.py:
  □ Add all write methods to GmailClient
  □ Add all write methods to AsyncGmailClient
□ Create tests/unit/test_composer.py
□ Create tests/unit/test_drafts.py
□ Create tests/unit/test_labels.py
```

**Testing:**
- Sync client works
- Async client works
- All operations covered

---

## Definition of Done

- [ ] All tasks checked off
- [ ] Send email works (plain, HTML, attachments)
- [ ] Reply threading works
- [ ] Draft CRUD works
- [ ] Label management works
- [ ] Archive/trash works
- [ ] Scope validation enforced
- [ ] All tests pass with 90%+ coverage

---

## Risks

| Risk | Mitigation |
|------|------------|
| Gmail send limits | Document limits, handle 429 |
| Attachment size limits | Validate before send, clear errors |
| Threading complexity | Test with real email threads |
