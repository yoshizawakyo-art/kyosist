-- ============================================================
-- task_users テーブル: Manus型タスク自動実行のユーザー情報管理
-- ============================================================
CREATE TABLE task_users (
    id         uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    uuid        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    username   text        NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(user_id)
);

-- ============================================================
-- task_history テーブル: タスク実行履歴管理
-- ============================================================
CREATE TABLE task_history (
    id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          uuid        NOT NULL REFERENCES task_users(id) ON DELETE CASCADE,
    task_type        text        NOT NULL CHECK (task_type IN ('browser', 'file', 'cli', 'db')),
    task_input       text        NOT NULL,
    executed_command jsonb,
    status           text        NOT NULL CHECK (status IN ('pending', 'running', 'success', 'error')) DEFAULT 'pending',
    result           jsonb,
    error_message    text,
    created_at       timestamptz NOT NULL DEFAULT now(),
    executed_at      timestamptz
);

-- ============================================================
-- task_skills テーブル: ユーザーカスタムスキル保存
-- ============================================================
CREATE TABLE task_skills (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid        NOT NULL REFERENCES task_users(id) ON DELETE CASCADE,
    skill_name  text        NOT NULL,
    description text,
    pattern     jsonb,
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE(user_id, skill_name)
);

-- ============================================================
-- インデックス（検索高速化）
-- ============================================================
CREATE INDEX idx_task_users_user_id ON task_users(user_id);
CREATE INDEX idx_task_history_user_id ON task_history(user_id);
CREATE INDEX idx_task_history_created_at ON task_history(created_at DESC);
CREATE INDEX idx_task_history_status ON task_history(status);
CREATE INDEX idx_task_history_task_type ON task_history(task_type);
CREATE INDEX idx_task_skills_user_id ON task_skills(user_id);
CREATE INDEX idx_task_skills_created_at ON task_skills(created_at DESC);

-- ============================================================
-- updated_at 自動更新トリガー
-- ============================================================
CREATE OR REPLACE FUNCTION update_task_users_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_task_users_updated_at
    BEFORE UPDATE ON task_users
    FOR EACH ROW
    EXECUTE FUNCTION update_task_users_updated_at();

-- ============================================================
-- RLS ポリシー: 認証ユーザーのみアクセス可能
-- ============================================================
ALTER TABLE task_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_skills ENABLE ROW LEVEL SECURITY;

-- task_users: 自分のユーザー情報のみ閲覧・編集可能
CREATE POLICY "user_own_task_user"
    ON task_users FOR ALL TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- task_history: 自分の履歴のみ閲覧・編集可能
CREATE POLICY "user_own_task_history"
    ON task_history FOR ALL TO authenticated
    USING (user_id IN (
        SELECT id FROM task_users WHERE user_id = auth.uid()
    ))
    WITH CHECK (user_id IN (
        SELECT id FROM task_users WHERE user_id = auth.uid()
    ));

-- task_skills: 自分のスキルのみ閲覧・編集可能
CREATE POLICY "user_own_task_skills"
    ON task_skills FOR ALL TO authenticated
    USING (user_id IN (
        SELECT id FROM task_users WHERE user_id = auth.uid()
    ))
    WITH CHECK (user_id IN (
        SELECT id FROM task_users WHERE user_id = auth.uid()
    ));
