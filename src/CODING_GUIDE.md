# コーディング規約・命名規則ガイド

## 📐 ファイル構成原則

### ディレクトリ構造
```
api/              → バックエンド（Python/FastAPI）
public/           → フロントエンド静的ファイル
├── index.html    → ルートページ（リダイレクト）
├── chat/         → チャットUI
│   ├── index.html
│   ├── main.js    → メインロジック
│   └── style.css  → UI スタイル
└── common/        → 共有コンポーネント・ユーティリティ
    ├── kyouUtils.js   → DOM構築関数群
    ├── kyouCommon.js  → サイドバーなど共通UI
    └── base.css       → グローバルスタイル
```

## 🏷️ 命名規則

### Python (api/index.py)

| 対象 | 規則 | 例 |
|------|------|-----|
| 関数 | snake_case | `get_supabase_client()`, `_insert_conversation()` |
| 定数 | UPPER_SNAKE_CASE | `CHAT_API_ENDPOINT` |
| クラス | PascalCase | `ChatRequest`, `ConversationResponse` |
| 私的関数 | _snake_case（先頭に _） | `_insert_message()`, `_fetch_conversations()` |
| 変数 | snake_case | `conv_id`, `message_text` |

### JavaScript (public/ フォルダ)

| 対象 | 規則 | 例 |
|------|------|-----|
| 関数 | camelCase | `buildPage()`, `appendChatMessage()` |
| イベントハンドラ | onPascalCase | `onWelcomeInputChange()`, `onSuggestionChipClick()` |
| 定数 | UPPER_SNAKE_CASE | `CHAT_API_ENDPOINT`, `SUGGESTION_CHIPS` |
| クラス | PascalCase | （基本的に使用しない - 関数型プログラミング） |
| 変数 | camelCase | `currentConversationId`, `isSendingMessage` |
| 私的関数 | （特に規則なし。モジュール内のみ） | `buildConversationItemElement()` |
| データ属性 | kebab-case | `data-text`, `data-conversation-id` |
| CSS クラス | kebab-case | `.msg-row`, `.history-item`, `.typing-dots` |
| ID 属性 | kebab-case | `id="chat-history"`, `id="typing-row"` |

### DOM 参照（refs オブジェクト）

```javascript
refs = {
  // 画面要素
  welcome: HTMLElement,        // ウェルカム画面
  chatView: HTMLElement,       // チャット画面
  bottomBar: HTMLElement,      // 下部入力バー
  
  // 入力要素
  welcomeInput: HTMLTextAreaElement,  // ウェルカム入力欄
  welcomeSend: HTMLButtonElement,     // ウェルカム送信ボタン
  chatInput: HTMLTextAreaElement,     // チャット入力欄
  chatSend: HTMLButtonElement,        // チャット送信ボタン
  
  // 表示領域
  messages: HTMLElement,       // メッセージ表示コンテナ
  
  // サイドバー
  chatHistory: HTMLElement,    // 会話履歴リスト
  newChatBtn: HTMLButtonElement, // 新規チャットボタン
}
```

## 📝 コメント規約

### ドキュメントコメント（JSDoc 形式）

```javascript
/**
 * 【関数の短い説明】
 *
 * 長い説明（必要に応じて）
 * - 処理フロー
 * - 副作用
 * - 注意点
 *
 * パラメータ:
 *   @param {type} paramName - 説明
 * 
 * 戻り値:
 *   @returns {type} 説明
 *
 * 例:
 *   functionName(arg) → 期待される動作
 */
function exampleFunction(param) {
  // ...
}
```

### インラインコメント

```javascript
// ━━ セクション区切り（視覚的に区別）━━━━━━━━━━━━━━━━━━━━━━━━━━
// グローバル状態変数

// 目的: API 呼び出し中かどうかを追跡
// 値: true（送信中） / false（待機中）
let isSendingMessage = false;

// ↓ または ─ の記号で重要な処理を強調
// ↓ ここでメッセージをクリア
refs.messages.innerHTML = "";

// 注釈付き（注意事項がある場合）
// 注: Supabase が自動的に id と timestamps を生成
result = client.table("conversations").insert({}).execute();
```

### Python コメント規約

```python
def get_supabase_client() -> Client:
    """
    【関数の役割】短い説明
    
    長い説明：
    - 何をするのか
    - なぜそれをするのか
    - 注意点
    
    Args:
        param1 (type): 説明
        param2 (type): 説明
    
    Returns:
        type: 説明
    
    Raises:
        ErrorType: エラーの説明
    
    Example:
        >>> client = get_supabase_client()
        >>> conversations = client.table("conversations").select("*").execute()
    """
    # コメント: 実装内容を短く記述
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_ANON_KEY"]
    return create_client(url, key)
```

## 🎨 CSS/HTML 規約

### CSS セクション区切り

```css
/* ════ セクション名 ════ */
/* セクション全体の説明がここに入る */

#element {
  /* CSS プロパティ */
  property: value;
  /* インラインコメント（必要に応じて） */
}

/* 状態変動やホバー効果 */
#element:hover {
  /* 変更内容の説明 */
  property: new-value;
}
```

### HTML コメント

```html
<!-- セクション区切り -->
<div id="main">
  
  <!-- 画面1: ウェルカム -->
  <div id="welcome">
    <!-- 大見出し -->
    <h1>タイトル</h1>
  </div>
  
  <!-- 画面2: チャット -->
  <div id="chat-view">
    <!-- メッセージ表示領域 -->
    <div id="messages"></div>
  </div>
  
</div>
```

## 🔄 処理フロー図の描き方

### テキストベース

```
┌─────────────────┐
│ ユーザー入力    │
└────────┬────────┘
         │
         ↓
    ┌─────────────────────┐
    │ イベント検証        │
    │ (値が空でないか)    │
    └────────┬────────────┘
             │
    ┌────────┴────────┐
    │ YES      │ NO   │
    ↓         ↓
┌────────┐  中止
│送信処理│
└────────┘
```

### 関数呼び出しチェーン

```
user input
  ↓
sendFromWelcomeScreen()
  ├─ appendChatMessage(text, "user")
  └─ sendMessageToAPI(text)
      ├─ showTypingIndicator()
      ├─ fetch("/api/chat")
      │   └─ API response
      ├─ hideTypingIndicator()
      ├─ appendChatMessage(reply, "bot")
      └─ updateSidebar()
```

## 🧪 テストポイント

### 単位テスト

```python
# api/index.py の関数テスト
def test_insert_conversation():
    client = get_supabase_client()
    result = _insert_conversation(client)
    assert result["id"] is not None
    assert result["created_at"] is not None
```

### 統合テスト

```javascript
// main.js の流れテスト
// 1. DOM構築 → refs が正しくセットされるか
// 2. イベント登録 → クリック・キー入力に応答するか
// 3. API通信 → サーバーと正確に通信できるか
// 4. UI更新 → メッセージ表示が正しいか
```

## ⚠️ よくあるミス

| ミス | 対策 |
|------|------|
| 関数名が曖昧（ex: `process()`, `handle()`) | 目的を明確にする（`sendMessageToAPI()` など） |
| コメントが古い（コード変更後更新忘れ） | コード変更時にコメントも一緒に更新 |
| 変数スコープの混乱 | グローバル変数と局所変数を明確に区別 |
| 非同期処理のエラーハンドリング忘れ | try-catch や .catch() を必ず付ける |
| HTML の id/class が不統一 | CSS と JavaScript の命名を統一 |

## 📚 参考資料

- [Google JavaScript Style Guide](https://google.github.io/styleguide/jsguide.html)
- [PEP 8 Python Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [MDN Web Docs - HTML/CSS/JavaScript](https://developer.mozilla.org/)

---

**作成日**: 2026年5月2日
