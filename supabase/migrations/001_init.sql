-- ============================================================
-- conversations テーブル: チャットスレッドを管理する
-- ============================================================
CREATE TABLE conversations (
    id         uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    title      text        NOT NULL DEFAULT '新しいチャット',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- messages テーブル: 各会話に属するメッセージを管理する
-- ============================================================
CREATE TABLE messages (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id uuid        NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            text        NOT NULL CHECK (role IN ('user', 'bot')),
    content         text        NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- インデックス
-- ============================================================
CREATE INDEX idx_messages_conversation_id ON messages (conversation_id);
CREATE INDEX idx_conversations_updated_at ON conversations (updated_at DESC);

-- ============================================================
-- updated_at 自動更新トリガー
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- RLS ポリシー
-- 現フェーズ: 認証なし → anon に全操作を許可
-- 将来の認証対応: conversations に user_id uuid REFERENCES auth.users(id) を追加後、
--   ポリシーを auth.uid() 条件に差し替えるだけで移行可能
-- ============================================================
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages      ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_all_conversations"
    ON conversations FOR ALL TO anon
    USING (true) WITH CHECK (true);

CREATE POLICY "anon_all_messages"
    ON messages FOR ALL TO anon
    USING (true) WITH CHECK (true);
