/**
 * Manus型タスク自動実行システムの型定義
 */

/**
 * TaskUser: ユーザー情報
 */
export interface TaskUser {
  id: string;
  user_id: string;
  username: string;
  created_at: string;
  updated_at: string;
}

/**
 * TaskHistory: タスク実行履歴
 */
export interface TaskHistory {
  id: string;
  user_id: string;
  task_type: 'browser' | 'file' | 'cli' | 'db';
  task_input: string;
  executed_command?: Record<string, any>;
  status: 'pending' | 'running' | 'success' | 'error';
  result?: Record<string, any>;
  error_message?: string;
  created_at: string;
  executed_at?: string;
}

/**
 * TaskSkill: ユーザーカスタムスキル
 */
export interface TaskSkill {
  id: string;
  user_id: string;
  skill_name: string;
  description?: string;
  pattern?: Record<string, any>;
  created_at: string;
}
