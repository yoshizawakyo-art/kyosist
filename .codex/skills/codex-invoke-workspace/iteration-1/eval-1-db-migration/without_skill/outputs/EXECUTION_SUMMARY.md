# Sessions Table Migration - Execution Summary

## Migration File
- **File**: `006_sessions.sql`
- **Location**: `supabase/migrations/006_sessions.sql`
- **Status**: Ready for deployment

## Schema Design

### Table: `sessions`

**Purpose**: Track active user sessions with token-based authentication support

**Columns**:
| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique session identifier |
| `user_id` | UUID | NOT NULL, REFERENCES users(id) ON DELETE CASCADE | Link to authenticated user |
| `token` | VARCHAR(512) | UNIQUE, NOT NULL | Session token (e.g., JWT or auth token) |
| `expires_at` | TIMESTAMP | NOT NULL | Session expiration time |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Session creation timestamp |

### Indexes Created

| Index Name | Columns | Use Case |
|------------|---------|----------|
| `idx_sessions_user_id` | `user_id` | Find all sessions for a user |
| `idx_sessions_token` | `token` | Validate/lookup sessions by token |
| `idx_sessions_expires_at` | `expires_at` | Cleanup queries for expired sessions |
| `idx_sessions_user_id_expires_at` | `user_id, expires_at` | Find valid (non-expired) sessions for a user |

### Foreign Key

- **Constraint**: `user_id` REFERENCES `users(id) ON DELETE CASCADE`
- **Effect**: When a user is deleted, all their sessions are automatically removed
- **Integrity**: Maintains referential integrity without orphaned records

## Design Rationale

1. **UUID for Primary Key**: Consistent with existing schema (users, password_reset_tokens)
2. **Token UNIQUE Constraint**: Prevents duplicate tokens; enables fast token validation
3. **Expires_at Index**: Critical for efficient session cleanup/expiration queries
4. **Composite Index (user_id, expires_at)**: Optimizes common query pattern: "Get all active sessions for user X"
5. **ON DELETE CASCADE**: When a user is deleted, sessions are automatically cleaned up
6. **VARCHAR(512) for Token**: Accommodates JWT tokens and other cryptographic tokens

## Migration Steps

To apply this migration:

```bash
# Using Supabase CLI
supabase migration up

# Or directly in Supabase dashboard:
# Navigate to SQL Editor → Create new query → Paste 006_sessions.sql → Execute
```

## Verification Queries

After migration, verify the table structure:

```sql
-- Check table structure
\d sessions;

-- Verify foreign key
SELECT constraint_name, table_name, column_name, foreign_table_name, foreign_column_name
FROM information_schema.key_column_usage
WHERE table_name = 'sessions' AND foreign_table_name IS NOT NULL;

-- Verify indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'sessions';
```

## Sample Usage

```sql
-- Insert a new session
INSERT INTO sessions (user_id, token, expires_at)
VALUES (
  '550e8400-e29b-41d4-a716-446655440000'::UUID,
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
  NOW() + INTERVAL '24 hours'
);

-- Find valid sessions for a user
SELECT * FROM sessions
WHERE user_id = '550e8400-e29b-41d4-a716-446655440000'::UUID
  AND expires_at > NOW()
ORDER BY created_at DESC;

-- Validate a token
SELECT * FROM sessions
WHERE token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
  AND expires_at > NOW();

-- Cleanup expired sessions
DELETE FROM sessions
WHERE expires_at < NOW();
```

## Notes

- **No Audit Logging**: The migration does not include audit tables. Add if compliance requires session history tracking.
- **No Rate Limiting**: Implement in application layer if needed.
- **Token Storage**: Consider encrypting tokens if sensitive data handling is required.
- **Session Limit**: Application layer should enforce max sessions per user if needed.
- **Created_at Purpose**: Useful for analytics (e.g., "sessions created in last 24 hours") and debugging.

## Dependencies

- Requires: `users` table (from migration 005_authentication.sql)
- No dependencies on other new migrations
- Safe to run in any environment where users table exists
