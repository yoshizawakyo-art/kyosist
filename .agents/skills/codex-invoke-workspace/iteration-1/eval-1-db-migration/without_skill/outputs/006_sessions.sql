-- sessions テーブル: ユーザーのアクティブセッション追跡
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token VARCHAR(512) UNIQUE NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- user_id でのセッション検索を高速化
CREATE INDEX idx_sessions_user_id ON sessions(user_id);

-- トークンでのセッション検索を高速化
CREATE INDEX idx_sessions_token ON sessions(token);

-- 期限切れセッションをクリーンアップするための複合インデックス
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- user_id と expires_at の複合インデックス（期限内の有効セッション取得時に活用）
CREATE INDEX idx_sessions_user_id_expires_at ON sessions(user_id, expires_at);
