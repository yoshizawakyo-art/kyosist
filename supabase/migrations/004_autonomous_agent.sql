-- ============================================================
-- sites テーブル: ブラウザ自動化で扱う対象サイトを管理する
-- ============================================================
CREATE TABLE sites (
    id                 uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    name               text        NOT NULL UNIQUE,
    category           text        NOT NULL DEFAULT 'business',
    base_url           text,
    allowed_domains    jsonb       NOT NULL DEFAULT '[]'::jsonb,
    blocked_site_rules jsonb       NOT NULL DEFAULT '[]'::jsonb,
    metadata_json      jsonb       NOT NULL DEFAULT '{}'::jsonb,
    created_at         timestamptz NOT NULL DEFAULT now(),
    updated_at         timestamptz NOT NULL DEFAULT now(),
    CHECK (base_url IS NULL OR base_url ~* '^https?://'),
    CHECK (jsonb_typeof(allowed_domains) = 'array'),
    CHECK (jsonb_typeof(blocked_site_rules) = 'array'),
    CHECK (jsonb_typeof(metadata_json) = 'object')
);

-- ============================================================
-- site_credentials テーブル: 対象サイトの暗号化済み認証情報を管理する
-- ============================================================
CREATE TABLE site_credentials (
    id                 uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id            uuid        NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    account_identifier text        NOT NULL,
    encrypted_secret   text        NOT NULL,
    encryption_version int         NOT NULL DEFAULT 1,
    key_id             text        NOT NULL,
    encryption_nonce   text        NOT NULL,
    metadata_json      jsonb       NOT NULL DEFAULT '{}'::jsonb,
    last_verified_at   timestamptz,
    created_at         timestamptz NOT NULL DEFAULT now(),
    updated_at         timestamptz NOT NULL DEFAULT now(),
    CHECK (btrim(account_identifier) <> ''),
    CHECK (btrim(encrypted_secret) <> ''),
    CHECK (encryption_version > 0),
    CHECK (btrim(key_id) <> ''),
    CHECK (btrim(encryption_nonce) <> ''),
    CHECK (jsonb_typeof(metadata_json) = 'object'),
    UNIQUE (site_id, account_identifier)
);

-- ============================================================
-- automation_tasks テーブル: 定型業務タスク設定を管理する
-- ============================================================
CREATE TABLE automation_tasks (
    id                 uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    name               text        NOT NULL,
    description        text        NOT NULL DEFAULT '',
    template_path      text,
    output_directory   text,
    filename_policy    jsonb       NOT NULL DEFAULT '{}'::jsonb,
    approval_policy    jsonb       NOT NULL DEFAULT '{}'::jsonb,
    blocked_site_ids   jsonb       NOT NULL DEFAULT '[]'::jsonb,
    blocked_site_rules jsonb       NOT NULL DEFAULT '[]'::jsonb,
    is_active          boolean     NOT NULL DEFAULT true,
    created_at         timestamptz NOT NULL DEFAULT now(),
    updated_at         timestamptz NOT NULL DEFAULT now(),
    CHECK (btrim(name) <> ''),
    CHECK (jsonb_typeof(filename_policy) = 'object'),
    CHECK (jsonb_typeof(approval_policy) = 'object'),
    CHECK (jsonb_typeof(blocked_site_ids) = 'array'),
    CHECK (jsonb_typeof(blocked_site_rules) = 'array')
);

-- ============================================================
-- automation_skills テーブル: 成果物出力までの自動化スキルを管理する
-- ============================================================
CREATE TABLE automation_skills (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         uuid        NOT NULL REFERENCES automation_tasks(id) ON DELETE CASCADE,
    name            text        NOT NULL,
    description     text        NOT NULL DEFAULT '',
    status          text        NOT NULL DEFAULT 'draft'
                                CHECK (status IN ('draft', 'active', 'paused', 'retired')),
    version         int         NOT NULL DEFAULT 1,
    definition_json jsonb       NOT NULL DEFAULT '{}'::jsonb,
    can_auto_run    boolean     NOT NULL DEFAULT false,
    last_run_at     timestamptz,
    success_count   int         NOT NULL DEFAULT 0,
    failure_count   int         NOT NULL DEFAULT 0,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CHECK (btrim(name) <> ''),
    CHECK (version > 0),
    CHECK (jsonb_typeof(definition_json) = 'object'),
    CHECK (success_count >= 0),
    CHECK (failure_count >= 0),
    UNIQUE (task_id, name, version)
);

-- ============================================================
-- automation_skill_steps テーブル: スキルの実行ステップを管理する
-- ============================================================
CREATE TABLE automation_skill_steps (
    id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id            uuid        NOT NULL REFERENCES automation_skills(id) ON DELETE CASCADE,
    step_order          int         NOT NULL,
    step_key            text,
    step_type           text        NOT NULL CHECK (
        step_type IN (
            'navigate',
            'login',
            'input',
            'click',
            'extract',
            'approve',
            'transform',
            'generate_file',
            'wait',
            'manual_intervention'
        )
    ),
    target_site_id      uuid        REFERENCES sites(id) ON DELETE SET NULL,
    instruction         text        NOT NULL,
    selector_or_locator text,
    input_mapping       jsonb       NOT NULL DEFAULT '{}'::jsonb,
    output_mapping      jsonb       NOT NULL DEFAULT '{}'::jsonb,
    retry_policy        jsonb       NOT NULL DEFAULT '{}'::jsonb,
    approval_required   boolean     NOT NULL DEFAULT false,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now(),
    CHECK (step_order > 0),
    CHECK (step_key IS NULL OR btrim(step_key) <> ''),
    CHECK (btrim(instruction) <> ''),
    CHECK (jsonb_typeof(input_mapping) = 'object'),
    CHECK (jsonb_typeof(output_mapping) = 'object'),
    CHECK (jsonb_typeof(retry_policy) = 'object'),
    UNIQUE (skill_id, step_order),
    UNIQUE (skill_id, step_key)
);

-- ============================================================
-- automation_task_runs テーブル: タスク実行履歴と再開状態を管理する
-- ============================================================
CREATE TABLE automation_task_runs (
    id                uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id           uuid        NOT NULL REFERENCES automation_tasks(id) ON DELETE CASCADE,
    skill_id          uuid        REFERENCES automation_skills(id) ON DELETE SET NULL,
    target_month      date        NOT NULL,
    status            text        NOT NULL DEFAULT 'queued'
                                  CHECK (
                                      status IN (
                                          'queued',
                                          'running',
                                          'waiting_approval',
                                          'waiting_manual_intervention',
                                          'paused',
                                          'succeeded',
                                          'failed',
                                          'cancelled'
                                      )
                                  ),
    current_step_id   uuid        REFERENCES automation_skill_steps(id) ON DELETE SET NULL,
    resume_state_json jsonb       NOT NULL DEFAULT '{}'::jsonb,
    output_file_path  text,
    started_at        timestamptz,
    finished_at       timestamptz,
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now(),
    CHECK (target_month = date_trunc('month', target_month)::date),
    CHECK (jsonb_typeof(resume_state_json) = 'object'),
    CHECK (finished_at IS NULL OR started_at IS NULL OR finished_at >= started_at)
);

-- ============================================================
-- automation_run_logs テーブル: 実行ログとユーザー向け復旧情報を管理する
-- ============================================================
CREATE TABLE automation_run_logs (
    id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id              uuid        NOT NULL REFERENCES automation_task_runs(id) ON DELETE CASCADE,
    step_id             uuid        REFERENCES automation_skill_steps(id) ON DELETE SET NULL,
    level               text        NOT NULL CHECK (level IN ('debug', 'info', 'warning', 'error')),
    message             text        NOT NULL,
    user_action_message text,
    details_json        jsonb       NOT NULL DEFAULT '{}'::jsonb,
    created_at          timestamptz NOT NULL DEFAULT now(),
    CHECK (btrim(message) <> ''),
    CHECK (jsonb_typeof(details_json) = 'object')
);

-- ============================================================
-- generated_files テーブル: 生成ファイルと同月再生成検知情報を管理する
-- ============================================================
CREATE TABLE generated_files (
    id            uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id        uuid        NOT NULL REFERENCES automation_task_runs(id) ON DELETE CASCADE,
    task_id       uuid        NOT NULL REFERENCES automation_tasks(id) ON DELETE CASCADE,
    target_month  date        NOT NULL,
    file_path     text        NOT NULL,
    file_name     text        NOT NULL,
    template_path text,
    file_kind     text        NOT NULL DEFAULT 'excel',
    metadata_json jsonb       NOT NULL DEFAULT '{}'::jsonb,
    created_at    timestamptz NOT NULL DEFAULT now(),
    CHECK (target_month = date_trunc('month', target_month)::date),
    CHECK (btrim(file_path) <> ''),
    CHECK (btrim(file_name) <> ''),
    CHECK (jsonb_typeof(metadata_json) = 'object')
);

-- ============================================================
-- インデックス
-- ============================================================
CREATE INDEX idx_sites_category ON sites (category);
CREATE INDEX idx_sites_allowed_domains ON sites USING gin (allowed_domains);

CREATE INDEX idx_site_credentials_site_id ON site_credentials (site_id);
CREATE INDEX idx_site_credentials_last_verified_at ON site_credentials (last_verified_at DESC);

CREATE INDEX idx_automation_tasks_created_at ON automation_tasks (created_at DESC);
CREATE INDEX idx_automation_tasks_blocked_site_ids ON automation_tasks USING gin (blocked_site_ids);

CREATE INDEX idx_automation_skills_task_id ON automation_skills (task_id);
CREATE INDEX idx_automation_skills_status ON automation_skills (status);

CREATE INDEX idx_automation_skill_steps_skill_id ON automation_skill_steps (skill_id, step_order);
CREATE INDEX idx_automation_skill_steps_target_site_id ON automation_skill_steps (target_site_id);

CREATE INDEX idx_automation_task_runs_task_id ON automation_task_runs (task_id, created_at DESC);
CREATE INDEX idx_automation_task_runs_skill_id ON automation_task_runs (skill_id);
CREATE INDEX idx_automation_task_runs_status ON automation_task_runs (status);
CREATE INDEX idx_automation_task_runs_current_step_id ON automation_task_runs (current_step_id);
CREATE INDEX idx_automation_task_runs_target_month ON automation_task_runs (task_id, target_month DESC);

CREATE INDEX idx_automation_run_logs_run_id ON automation_run_logs (run_id, created_at);
CREATE INDEX idx_automation_run_logs_step_id ON automation_run_logs (step_id);
CREATE INDEX idx_automation_run_logs_level ON automation_run_logs (level);

CREATE INDEX idx_generated_files_run_id ON generated_files (run_id);
CREATE INDEX idx_generated_files_task_month ON generated_files (task_id, target_month DESC);
CREATE INDEX idx_generated_files_file_path ON generated_files (file_path);

-- ============================================================
-- updated_at 自動更新トリガー
-- ============================================================
CREATE TRIGGER trg_sites_updated_at
    BEFORE UPDATE ON sites
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_site_credentials_updated_at
    BEFORE UPDATE ON site_credentials
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_automation_tasks_updated_at
    BEFORE UPDATE ON automation_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_automation_skills_updated_at
    BEFORE UPDATE ON automation_skills
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_automation_skill_steps_updated_at
    BEFORE UPDATE ON automation_skill_steps
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_automation_task_runs_updated_at
    BEFORE UPDATE ON automation_task_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- RLS ポリシー
-- 現フェーズ: 認証なし → anon に全操作を許可
-- 将来の認証対応: 各テーブルに user_id uuid REFERENCES auth.users(id) を追加後、
--   ポリシーを auth.uid() 条件に差し替える
-- ============================================================
ALTER TABLE sites                  ENABLE ROW LEVEL SECURITY;
ALTER TABLE site_credentials       ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_tasks       ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_skills      ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_skill_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_task_runs   ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_run_logs    ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_files        ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_all_sites"
    ON sites FOR ALL TO anon
    USING (true) WITH CHECK (true);

CREATE POLICY "anon_all_site_credentials"
    ON site_credentials FOR ALL TO anon
    USING (true) WITH CHECK (true);

CREATE POLICY "anon_all_automation_tasks"
    ON automation_tasks FOR ALL TO anon
    USING (true) WITH CHECK (true);

CREATE POLICY "anon_all_automation_skills"
    ON automation_skills FOR ALL TO anon
    USING (true) WITH CHECK (true);

CREATE POLICY "anon_all_automation_skill_steps"
    ON automation_skill_steps FOR ALL TO anon
    USING (true) WITH CHECK (true);

CREATE POLICY "anon_all_automation_task_runs"
    ON automation_task_runs FOR ALL TO anon
    USING (true) WITH CHECK (true);

CREATE POLICY "anon_all_automation_run_logs"
    ON automation_run_logs FOR ALL TO anon
    USING (true) WITH CHECK (true);

CREATE POLICY "anon_all_generated_files"
    ON generated_files FOR ALL TO anon
    USING (true) WITH CHECK (true);
