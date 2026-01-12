# Phase 5: Supabase Storage Backend

**Duration:** Week 5
**Dependencies:** Phase 4 (Gmail Write)

---

## Objectives

1. Implement Supabase storage backend
2. Create migration scripts
3. Add connection pooling
4. Test production-grade storage

---

## Deliverables

- [ ] SupabaseBackend implementing StorageBackend
- [ ] Migration scripts for Supabase
- [ ] Connection pooling support
- [ ] Integration tests with Supabase
- [ ] Documentation for Supabase setup

---

## Task Breakdown

### 5.1 Supabase Client Setup

```
□ Create gmail_multi_user/storage/supabase.py
  □ SupabaseBackend class
  □ __init__(supabase_url, supabase_key)
    □ Initialize Supabase client
    □ Configure connection pool
  □ initialize() - verify connection
  □ close() - cleanup
```

**Testing:**
- Connection established
- Invalid credentials handled

### 5.2 User Operations

```
□ Add to supabase.py:
  □ get_or_create_user(external_user_id, email)
    □ Upsert to users table
    □ Return User object
  □ get_user_by_external_id(external_user_id)
    □ Query users table
    □ Return User or None
  □ list_users()
    □ Query all users
    □ Return list[User]
```

**Testing:**
- User created on first call
- User returned on subsequent calls
- List returns all users

### 5.3 Connection Operations

```
□ Add to supabase.py:
  □ create_connection(user_id, gmail_address, ...)
    □ Insert into gmail_connections
    □ Return Connection
  □ get_connection(connection_id)
    □ Query by ID
    □ Return Connection or None
  □ list_connections(user_id, include_inactive)
    □ Query with optional filters
    □ Return list[Connection]
  □ update_connection_tokens(connection_id, access_token, expires_at)
    □ Update token fields
  □ deactivate_connection(connection_id)
    □ Set is_active = False
  □ delete_connection(connection_id)
    □ Delete row
```

**Testing:**
- CRUD operations work
- Filtering works
- Unique constraint enforced

### 5.4 OAuth State Operations

```
□ Add to supabase.py:
  □ create_oauth_state(state, user_id, ...)
    □ Insert into oauth_states
  □ get_oauth_state(state)
    □ Query by state
    □ Return OAuthState or None
  □ delete_oauth_state(state)
    □ Delete row
  □ cleanup_expired_states()
    □ Delete where expires_at < now
    □ Return count deleted
```

**Testing:**
- State created and retrieved
- Expired states cleaned up

### 5.5 Migration Scripts

```
□ Create migrations/supabase/001_initial.sql
  □ Create users table
  □ Create gmail_connections table
  □ Create oauth_states table
  □ Create indexes
  □ Create update_timestamp trigger
□ Update gmail_multi_user/storage/migrations.py
  □ Support Supabase migrations
  □ Track applied migrations
```

**Testing:**
- Migration applies cleanly
- Idempotent (can run twice)
- Rollback possible

### 5.6 Storage Factory Update

```
□ Update gmail_multi_user/storage/factory.py:
  □ Add supabase case
  □ Validate config for supabase
  □ Create SupabaseBackend
```

**Testing:**
- Factory creates correct backend
- Missing config raises error

### 5.7 Connection Pooling

```
□ Configure Supabase client for pooling
□ Handle connection limits
□ Implement retry logic for pool exhaustion
□ Add connection timeout handling
```

**Testing:**
- High concurrency handled
- Pool exhaustion graceful
- Timeouts don't hang

### 5.8 Integration Tests

```
□ Create tests/integration/test_storage_supabase.py
  □ Use test Supabase project (CI)
  □ Test all CRUD operations
  □ Test concurrent access
  □ Test connection pooling
□ Set up Supabase test project
  □ Configure GitHub Secrets
  □ Run migrations in CI
```

**Testing:**
- All operations work against real Supabase
- Concurrent access works
- CI tests pass

### 5.9 Documentation

```
□ Create docs/supabase-setup.md
  □ Create Supabase project
  □ Get service role key
  □ Run migrations
  □ Configure in gmail_config.yaml
  □ Troubleshooting
```

---

## Definition of Done

- [ ] All tasks checked off
- [ ] SupabaseBackend fully functional
- [ ] Migrations apply cleanly
- [ ] Connection pooling works
- [ ] Integration tests pass
- [ ] Setup documentation complete
- [ ] Can switch from SQLite to Supabase seamlessly

---

## Risks

| Risk | Mitigation |
|------|------------|
| Supabase API changes | Pin client version, test regularly |
| Rate limits | Implement retry, document limits |
| Test isolation | Use separate test project |
