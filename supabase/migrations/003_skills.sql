-- ============================================================
-- skills テーブル: 業務自動化スキルを管理する
-- ============================================================
CREATE TABLE skills (
    id                   uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    name                 text        NOT NULL,
    description          text        NOT NULL,
    action_url           text        NOT NULL,
    action_method        text        NOT NULL DEFAULT 'POST',
    action_body_template text        NOT NULL DEFAULT '',
    created_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_skills_created_at ON skills (created_at DESC);

-- ============================================================
-- RLS ポリシー: 現フェーズは認証なし → anon に全操作を許可
-- ============================================================
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_all_skills"
    ON skills FOR ALL TO anon
    USING (true) WITH CHECK (true);
