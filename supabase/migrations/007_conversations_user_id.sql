ALTER TABLE conversations
  ADD COLUMN user_id UUID REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX idx_conversations_user_id
  ON conversations (user_id, updated_at DESC);
