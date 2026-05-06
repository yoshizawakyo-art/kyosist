# サブエージェント選択ガイド

## タスク別 最適サブエージェント一覧

| タスクの性質 | 使うべきサブエージェント |
|---|---|
| コードベース探索・ファイル検索 | `Explore` |
| 実装計画・アーキテクチャ設計 | `Plan` |
| バックエンドAPI実装・レビュー | `backend-specialist` |
| フロントエンドUI実装 | `frontend-ui-specialist` |
| DB設計・クエリ最適化 | `db-architect` |
| インフラ・デプロイ・CI/CD | `infra-devops-engineer` |
| PDCAのCheckフェーズ（実装後レビュー） | `pdca-check-reviewer` |
| コードレビュー（アドホック・品質確認） | `senior-code-reviewer` |
| 技術選定・アーキテクチャ比較 | `tech-lead-researcher` |
| Claude Code/API の使い方 | `claude-code-guide` |
| 上記に当てはまらない汎用タスク | `general-purpose` |

## 選択の原則

1. **タスクの性質を先に判断する** — 調査/実装/設計/レビューのどれかを特定してからエージェントを選ぶ
2. **専門エージェント優先** — 専門エージェントが存在する場合は必ずそれを使う（`general-purpose` を安易に使わない）
3. **並列実行の活用** — 独立したタスクは複数エージェントを同時に起動して効率化する

## 3エージェントパターン（Gen/Eval 分離）

LLMは自分の出力を過剰評価する傾向があるため、**生成と評価を同一エージェントに担わせない**:

| 役割 | 担当 | 特性 |
|---|---|---|
| **プランナー** | `Plan` / `tech-lead-researcher` | 俯瞰・タスク分解・計画立案 |
| **ジェネレーター** | 専門実装エージェント | 計画に基づく成果物の作成 |
| **エバリューエーター（PDCAワークフロー）** | `pdca-check-reviewer` | 超厳格コードレビュー（CHECK OK/NG返却） |
| **エバリューエーター（汎用）** | `senior-code-reviewer` | 懐疑的な視点での独立検証 |

適用場面:
- 複雑な実装タスク → Plan で計画 → 専門エージェントで実装 → senior-code-reviewer でレビュー
- 設計判断 → tech-lead-researcher で比較 → backend-specialist で実装 → senior-code-reviewer で検証
