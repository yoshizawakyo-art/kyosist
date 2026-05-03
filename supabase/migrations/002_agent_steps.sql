-- ============================================================
-- agent_steps テーブル: ReActエージェントの思考ステップを記録する
-- ============================================================
-- step_type の値:
--   thought     : エージェントの思考・分析
--   action      : ツール呼び出し（web_search, notion_write 等）
--   observation : ツールの実行結果
--   answer      : 最終回答
-- ============================================================
CREATE TABLE agent_steps (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id  uuid        NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    step_index  int         NOT NULL,
    step_type   text        NOT NULL CHECK (step_type IN ('thought', 'action', 'observation', 'answer')),
    content     text        NOT NULL,
    tool_name   text,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_agent_steps_message_id ON agent_steps (message_id, step_index);

-- ============================================================
-- RLS ポリシー（現フェーズ: 認証なし → anon に全操作を許可）
-- ============================================================
ALTER TABLE agent_steps ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_all_agent_steps"
    ON agent_steps FOR ALL TO anon
    USING (true) WITH CHECK (true);
