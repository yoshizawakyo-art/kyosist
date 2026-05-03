# Kyosist AI チャットシステム - プロジェクト全体ドキュメント

## 📋 プロジェクト概要

Kyosist AI は、FastAPI + Supabase + Vanilla JavaScript で構築された、シンプルで拡張性の高いAIチャットシステムです。
ユーザーが AI と対話し、会話履歴が自動的にデータベースに保存される機能を備えています。

---

## 📁 ディレクトリ構造

```
src/
├── api/
│   └── index.py                 # バックエンド API（FastAPI）
├── public/
│   ├── index.html               # リダイレクトページ（/ → /chat/）
│   ├── chat/
│   │   ├── index.html           # チャットUI メインページ
│   │   ├── main.js              # チャット画面のロジック・イベント処理
│   │   └── style.css            # チャット UI のスタイル
│   └── common/
│       ├── kyouUtils.js         # DOM構築ユーティリティ関数
│       ├── kyouCommon.js        # 共通UI コンポーネント（サイドバー等）
│       └── base.css             # グローバル基本スタイル
└── vercel.json                  # Vercel デプロイ設定（ルーティング）
```

---

## 🔧 各ファイルの役割

### バックエンド

#### `api/index.py` - FastAPI サーバー
**目的**: REST API エンドポイント提供、データベース操作、ファイル配信

**主な処理**:
- **CORS 設定**: すべてのオリジンからのリクエストを許可
- **静的ファイル配信**: HTML/JS/CSS をクライアントに提供
- **Pydantic モデル**: リクエスト/レスポンスのバリデーション
- **Supabase クライアント**: 環境変数から認証情報を取得

**エンドポイント一覧**:
| メソッド | エンドポイント | 役割 |
|---------|--------------|------|
| POST | `/api/conversations` | 新規会話を作成 |
| GET | `/api/conversations` | 会話一覧（最近50件）を取得 |
| GET | `/api/conversations/{id}/messages` | 指定会話のメッセージを取得 |
| POST | `/api/chat` | メッセージ送信・AI応答生成・保存 |

**データベース要件**:
- Supabase PostgreSQL に以下テーブルが必要:
  - `conversations`: 会話スレッド（id, title, created_at, updated_at）
  - `messages`: 個別メッセージ（id, conversation_id, role, content, created_at）

---

### フロントエンド

#### `public/index.html` - リダイレクトページ
**目的**: ルートパス (/) にアクセスされた場合、/chat/ へリダイレクト

**リダイレクト方法**:
1. HTML の `<meta http-equiv="refresh">` タグ
2. JavaScript の `location.replace()` （フォールバック）

---

#### `public/chat/index.html` - メインページ
**目的**: チャット UI のマークアップ

**構成要素**:
- `<link>` タグで CSS を読み込み
- `<script type="module">` で `main.js` を読み込み

---

#### `public/chat/main.js` - チャット UI ロジック
**目的**: UI 状態管理、イベント処理、API 通信

**グローバル状態変数**:
- `isSendingMessage`: API 呼び出し中フラグ（重複送信防止）
- `isInChatMode`: 画面表示モード（ウェルカム ↔ チャット）
- `currentConversationId`: 現在の会話 ID
- `refs`: DOM 要素への参照

**主要関数グループ**:

1. **DOM 構築関数**
   - `buildWelcomeScreen()`: ウェルカム画面
   - `buildChatView()`: メッセージ表示領域
   - `buildBottomInputBar()`: 入力バー
   - `buildPage()`: ページ全体

2. **UI 更新関数**
   - `appendChatMessage()`: メッセージを画面に追加
   - `showTypingIndicator()`: タイピング表示
   - `hideTypingIndicator()`: タイピング非表示
   - `resizeTextareaHeight()`: テキストエリアの自動高さ調整
   - `enterChatMode()`: チャット画面に切り替え
   - `resetToWelcomeScreen()`: ウェルカム画面に戻す

3. **API 通信関数**
   - `sendMessageToAPI()`: メッセージを送信・応答を処理
   - `loadConversationMessages()`: 過去会話を読み込み

4. **イベントハンドラ**
   - `onWelcomeInputChange()`: テキスト入力時
   - `onWelcomeInputKeydown()`: Enter キーで送信
   - `onChatInputChange()`: テキスト入力時
   - `onChatInputKeydown()`: Enter キーで送信
   - `onSuggestionChipClick()`: 提案チップクリック

5. **初期化**
   - `buildPage()`: DOM 構築
   - `attachEventListeners()`: イベントリスナー登録
   - `loadConversationsIntoSidebar()`: 会話一覧を読み込み

---

#### `public/chat/style.css` - チャット UI スタイル
**目的**: ビジュアルデザイン定義

**主要セクション**:
- **レイアウト**: `#main`, `#welcome`, `#chat-view`, `#bottom-bar`
- **ウェルカム画面**: アイキャッチ、入力ボックス、提案チップ
- **メッセージ表示**: メッセージバブル（ユーザー/AI）、タイピングインジケーター
- **色定義**: CSS カスタムプロパティ（`--user-bubble`, `--bot-bubble` 等）

---

#### `public/common/kyouUtils.js` - DOM 構築ユーティリティ
**目的**: 共通的な DOM 操作関数を提供

**提供関数**:
- `buildElement(tag, className, domProps)`: HTML 要素を生成
- `buildSidebarIcon(svgMarkup)`: SVG アイコンを生成
- `buildSendButton(buttonId)`: 送信ボタンを生成
- `buildInputBox(textareaId, buttonId, placeholder, boxClass)`: テキスト入力ボックスを生成

---

#### `public/common/kyouCommon.js` - 共通 UI コンポーネント
**目的**: サイドバー・会話履歴管理

**提供関数**:
- `buildSidebar(refs)`: サイドバーを生成
- `loadConversationsIntoSidebar(container, callback)`: API から会話一覧を取得・表示
- `prependConversationItem(container, conversation, callback)`: 新規会話を先頭に追加
- `generatePrimaryKey(tablePrefix)`: タイムスタンプベースの ID を生成

---

## 🔌 API 仕様詳細

### 1. 新規会話作成

```http
POST /api/conversations
```

**リクエスト**: ボディなし

**レスポンス**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "",
  "created_at": "2026-05-02T12:30:45.123Z",
  "updated_at": "2026-05-02T12:30:45.123Z"
}
```

---

### 2. 会話一覧取得

```http
GET /api/conversations
```

**レスポンス**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "コードを書いてほしい",
    "created_at": "2026-05-02T12:30:45.123Z",
    "updated_at": "2026-05-02T12:35:10.456Z"
  },
  ...
]
```

---

### 3. メッセージ一覧取得

```http
GET /api/conversations/{conversation_id}/messages
```

**レスポンス**:
```json
[
  {
    "id": "msg1",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "role": "user",
    "content": "Hello, how are you?",
    "created_at": "2026-05-02T12:30:50.000Z"
  },
  {
    "id": "msg2",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "role": "bot",
    "content": "I'm doing well, thank you!",
    "created_at": "2026-05-02T12:30:55.000Z"
  }
]
```

---

### 4. メッセージ送信・AI応答取得

```http
POST /api/chat
Content-Type: application/json

{
  "message": "Hello!",
  "conversation_id": null
}
```

**リクエスト説明**:
- `message`: ユーザーのメッセージ（必須）
- `conversation_id`: 既存会話の ID、または null で新規会話

**レスポンス**:
```json
{
  "reply": "Pythonからの返信: Hello!",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## 🚀 デプロイ設定

### `vercel.json` - Vercel ルーティング設定

**設定内容**:
| ルート | 対応先 | 説明 |
|------|------|------|
| `/api/(.*)` | `/api/index.py` | 全 API リクエストを Python サーバーへ |
| `/favicon.ico` | `/public/favicon.png` | ファイコン |
| `/chat/?$` | `/public/chat/index.html` | チャットページ（ルートパス） |
| `/chat/(.*)` | `/public/chat/$1` | チャットページ関連ファイル |
| `/` | `/public/index.html` | ホームページ（リダイレクト） |
| `/(.*)` | `/public/$1` | その他すべてを public フォルダから配信 |

---

## 🔐 環境変数

バックエンド（`api/index.py`）で必要な環境変数:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
```

取得方法:
1. [Supabase](https://supabase.com) でプロジェクトを作成
2. Project Settings → API タブから URL と Key をコピー
3. Vercel のプロジェクト設定から環境変数を追加

---

## 📚 開発フロー

### ローカル開発

```bash
# 1. 環境変数を .env ファイルに設定
SUPABASE_URL=...
SUPABASE_ANON_KEY=...

# 2. Python 環境構築
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install fastapi supabase

# 3. サーバー起動
uvicorn api.index:app --reload

# 4. ブラウザでアクセス
http://localhost:8000
```

### Vercel へのデプロイ

```bash
# 1. GitHub リポジトリにコミット
git add .
git commit -m "Add chat feature"
git push

# 2. Vercel にログイン・プロジェクト接続
vercel link

# 3. 環境変数を設定
vercel env add SUPABASE_URL
vercel env add SUPABASE_ANON_KEY

# 4. デプロイ
vercel
```

---

## 🐛 トラブルシューティング

### API 接続エラー

**症状**: "会話の読み込みに失敗しました"

**原因と対策**:
1. Supabase 環境変数が正しく設定されているか確認
2. Supabase テーブルが正しく作成されているか確認
3. CORS 設定を確認（`api/index.py` の CORSMiddleware）

### メッセージが保存されない

**原因と対策**:
1. Supabase の接続を確認
2. テーブルの権限（RLS ポリシー）を確認
3. ネットワークタブで API レスポンスを確認

### 画面がリセットしない

**原因と対策**:
1. `resetToWelcomeScreen()` の実行確認
2. `refs` オブジェクトが正しく初期化されているか
3. ブラウザコンソールでエラーを確認

---

##🎨 UI/UX ポイント

- **ウェルカム画面**: 初回ユーザーに対話の提案を表示
- **提案チップ**: タップで内容が自動入力（キーボード入力の手間削減）
- **テキスト自動高さ調整**: 改行を促し、ユーザーフレンドリーに
- **タイピングインジケーター**: AI が応答生成中であることを視覚的に表現
- **会話履歴管理**: 最近の会話が優先表示される
- **キーボード操作**: Shift+Enter で改行、Enter で送信

---

## 📝 ライセンス

MIT License（ご自由に使用・改変可）

---

## 💡 今後の拡張案

- [ ] リアルな OpenAI API 統合
- [ ] 複数言語対応
- [ ] Dark Mode
- [ ] メッセージ検索機能
- [ ] 画像アップロード・表示
- [ ] 音声入力・出力
- [ ] ユーザー認証システム

---

**更新日**: 2026年5月2日

