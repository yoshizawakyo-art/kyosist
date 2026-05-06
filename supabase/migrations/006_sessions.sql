-- ============================================================
-- sessions table: tracks active user login sessions
-- ============================================================
CREATE TABLE sessions (
    id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      uuid        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash   text        NOT NULL UNIQUE,
    user_agent   text,
    ip_address   inet,
    expires_at   timestamptz NOT NULL,
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    revoked_at   timestamptz,
    created_at   timestamptz NOT NULL DEFAULT now(),
    updated_at   timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT sessions_expires_after_created
        CHECK (expires_at > created_at),
    CONSTRAINT sessions_revoked_after_created
        CHECK (revoked_at IS NULL OR revoked_at >= created_at)
);

CREATE INDEX idx_sessions_user_id ON sessions (user_id);
CREATE INDEX idx_sessions_active_by_user
    ON sessions (user_id, expires_at DESC)
    WHERE revoked_at IS NULL;
CREATE INDEX idx_sessions_expires_at ON sessions (expires_at);

CREATE TRIGGER trg_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_all_sessions"
    ON sessions FOR ALL TO anon
    USING (true) WITH CHECK (true);
