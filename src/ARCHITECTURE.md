# Kyosist AI チャットシステム - アーキテクチャ詳細

## 📐 システムアーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                         クライアント層                          │
│  (ブラウザ - Vanilla JavaScript)                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  public/chat/index.html                                          │
│          ↓                                                        │
│  public/chat/main.js (メインロジック)                            │
│  ├─ buildPage() ... DOM構築                                      │
│  ├─ appendChatMessage() ... メッセージ描画                       │
│  ├─ sendMessageToAPI() ... API通信                               │
│  └─ イベントハンドラ... ユーザー入力処理                         │
│                                                                   │
│  public/common/kyouUtils.js (DOM構築関数)                        │
│  ├─ buildElement() ... 要素生成                                  │
│  ├─ buildSidebarIcon() ... SVGアイコン生成                       │
│  └─ buildInputBox() ... 入力ボックス生成                         │
│                                                                   │
│  public/common/kyouCommon.js (共通コンポーネント)                │
│  ├─ buildSidebar() ... サイドバー生成                            │
│  ├─ loadConversationsIntoSidebar() ... 会話一覧取得              │
│  └─ prependConversationItem() ... 新規会話追加                   │
│                                                                   │
│  public/chat/style.css (スタイル定義)                            │
│  public/common/base.css (基本スタイル)                           │
│                                                                   │
└────────────────────────────┬────────────────────────────────────┘\n                             │ HTTP/JSON\n                             ↓\n┌─────────────────────────────────────────────────────────────────┐\n│                       サーバー層                                │\n│  (FastAPI - Python)                                             │\n├─────────────────────────────────────────────────────────────────┤\n│                                                                   │\n│  api/index.py                                                    │\n│  ├─ CORS設定 ... クロスオリジンリクエスト許可                   │\n│  ├─ 静的ファイル配信 ... public フォルダの HTML/JS/CSS          │\n│  │                                                               │\n│  ├─ エンドポイント:                                              │\n│  │  POST /api/conversations ... 新規会話作成                    │\n│  │  GET /api/conversations ... 会話一覧取得                     │\n│  │  GET /api/conversations/{id}/messages ... メッセージ取得     │\n│  │  POST /api/chat ... メッセージ送信・応答生成                │\n│  │                                                               │\n│  ├─ Pydantic モデル ... リクエスト/レスポンス定義               │\n│  │  ├─ ChatRequest                                               │\n│  │  ├─ ConversationResponse                                      │\n│  │  ├─ MessageResponse                                           │\n│  │  └─ ChatResponse                                              │\n│  │                                                               │\n│  └─ DB ヘルパー関数 ... Supabase 操作                            │\n│     ├─ _insert_conversation() ... 新規会話挿入                  │\n│     ├─ _fetch_conversations() ... 会話一覧取得                  │\n│     ├─ _fetch_messages() ... メッセージ取得                     │\n│     ├─ _insert_message() ... メッセージ挿入                     │\n│     └─ _touch_conversation() ... 会話の更新日時更新             │\n│                                                                   │\n└────────────────────────────┬────────────────────────────────────┘\n                             │ SQL Query\n                             ↓\n┌─────────────────────────────────────────────────────────────────┐\n│                       データベース層                             │\n│  (Supabase PostgreSQL)                                          │\n├─────────────────────────────────────────────────────────────────┤\n│                                                                   │\n│  conversations テーブル                                         │\n│  ├─ id (UUID) ... 主キー                                        │\n│  ├─ title (text) ... 会話のタイトル                             │\n│  ├─ created_at (timestamp) ... 作成日時                         │\n│  └─ updated_at (timestamp) ... 最終更新日時                     │\n│                                                                   │\n│  messages テーブル                                              │\n│  ├─ id (UUID) ... 主キー                                        │\n│  ├─ conversation_id (UUID) ... 外部キー → conversations.id      │\n│  ├─ role (text) ... \"user\" または \"bot\"                        │\n│  ├─ content (text) ... メッセージ本文                           │\n│  └─ created_at (timestamp) ... 作成日時                         │\n│                                                                   │\n└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 ユーザーフロー

### パターン1: ウェルカム画面から新規メッセージ送信

```
1. ページ読み込み
   └→ buildPage() で DOM 構築
   └→ attachEventListeners() で イベント登録
   └→ loadConversationsIntoSidebar() で 過去会話読み込み

2. ウェルカム入力欄に文字入力
   └→ onWelcomeInputChange() 発火
   └→ resizeTextareaHeight() で高さ調整

3. Enter キー または 「送信」ボタン
   └→ onWelcomeInputKeydown() / sendFromWelcomeScreen() 発火
   └→ 入力値をクリア
   └→ enterChatMode() で画面切り替え
   └→ appendChatMessage(text, "user") で ユーザーメッセージ表示
   └→ sendMessageToAPI(text) を呼び出し

4. API 通信
   └→ showTypingIndicator() で タイピング表示開始
   └→ refs.welcomeSend.disabled = true （送信ボタン無効化）
   └→ POST /api/chat へリクエスト送信
      └→ body: { message: text, conversation_id: null }

5. API レスポンス受取
   └→ responseData.conversation_id を currentConversationId に保存
   └→ hideTypingIndicator() で タイピング非表示
   └→ appendChatMessage(reply, "bot") で AI応答表示
   └→ prependConversationItem() で サイドバー先頭に新規会話を追加
   └→ refs.welcomeSend.disabled = false （送信ボタン有効化）
```

### パターン2: 過去会話をサイドバーから選択

```
1. サイドバーの会話アイテムをクリック
   └→ onSuggestionChipClick() 発火
   └→ 会話ID を取得
   └→ loadConversationMessages(conversationId) を呼び出し

2. メッセージ読み込み
   └→ currentConversationId に会話ID を保存
   └→ isInChatMode が false なら enterChatMode() を実行
   └→ refs.messages.innerHTML = "" でリセット
   └→ GET /api/conversations/{conversationId}/messages へリクエスト

3. メッセージ表示
   └→ 返されたメッセージを順番に appendChatMessage() で表示
   └→ エラーの場合は エラーメッセージを表示

4. 新規メッセージ送信
   └→ パターン1 の 手順 2 以降と同じ
   └→ (conversation_id は保存されているため、同じ会話に追加される)
```

---

## 💾 データフロー: メッセージ保存

### クライアント → サーバー → DB

```
クライアント (main.js)
  ↓
POST /api/chat
{
  "message": "ユーザーの入力",
  "conversation_id": "550e8400-..." または null
}
  ↓
サーバー (api/index.py - chat() 関数)
  1. conversation_id が null ?
     ├→ YES: _insert_conversation() で新規会話作成
     └→ NO: 指定された conversation_id を使用
  2. _insert_message(role="user", content=message)
     └→ ユーザーメッセージを messages テーブルに挿入
  3. reply = "...AI応答..." を生成
  4. _insert_message(role="bot", content=reply)
     └→ AI応答を messages テーブルに挿入
  5. _touch_conversation()
     └→ conversations テーブルの updated_at を現在時刻に更新
  6. ChatResponse を返す
  ↓
DB (Supabase PostgreSQL)
  conversations テーブル (updated_at が更新 → 一覧で新順に)
  messages テーブル (2行追加: ユーザーメッセージ + AI応答)
  ↓
クライアント (main.js)
  responseData.conversation_id と responseData.reply を取得
  → UI に表示
```

---

## 🎯 主要な状態管理パターン

### グローバル状態 (main.js)

```javascript
// 1. UI モード状態
isInChatMode: boolean
├─ true  → チャット画面表示（ウェルカム非表示）
└─ false → ウェルカム画面表示（チャット非表示）

// 2. 会話 ID 状態
currentConversationId: string | null
├─ null → 新規会話作成予定、またはウェルカム画面
└─ UUID → その会話のメッセージを表示中

// 3. 送信状態
isSendingMessage: boolean
├─ true  → API呼び出し中（重複送信防止、ボタン無効化）
└─ false → 待機中（送信可能）

// 4. DOM 参照
refs: object
├─ refs.messages → メッセージ表示領域
├─ refs.chatInput → チャット入力欄
├─ refs.welcomeInput → ウェルカム入力欄
├─ refs.chatView → チャット画面コンテナ
├─ refs.welcome → ウェルカム画面コンテナ
├─ refs.bottomBar → 下部入力バー
├─ refs.chatHistory → サイドバー会話一覧
└─ refs.newChatBtn → 新規チャットボタン
```

### 状態遷移図

```
┌──────────────────────┐
│  ページ読み込み       │
│ isInChatMode = false │
└──────────────┬───────┘
               │
               ↓
      ┌────────────────┐
      │ ウェルカム画面 │◄──────────────────┐
      │ 会話ID = null  │                   │
      └────────┬───────┘                   │
               │                           │
    [メッセージ送信] または [チップクリック]
               │                           │
               ↓                           │
    ┌──────────────────────┐        「新規チャット」ボタン
    │   API呼び出し中      │        (resetToWelcomeScreen)
    │ isSendingMessage=true│               │
    └──────────┬───────────┘               │
               │                           │
     [API レスポンス受取]                  │
               │                           │
               ↓                           │
      ┌────────────────────┐              │
      │   チャット画面     │              │
      │ 会話ID = UUID    │──────────────┘
      │ isInChatMode=true  │
      │ isSendingMessage=false│
      └────────┬───────────┘
               │
   [継続してメッセージ送信]
               │
               └─────────► (同じ会話へ追加)
```

---

## 🔌 API エンドポイント実装詳細

### POST /api/chat

**処理ロジック** (asyncio.to_thread で非同期化):

```python
async def chat(req: ChatRequest) -> ChatResponse:
    client = get_supabase_client()
    
    # 1. 会話ID の決定
    if req.conversation_id is None:
        # 新規会話: conversations テーブルに行を挿入
        conv_row = await asyncio.to_thread(_insert_conversation, client)
        conv_id = conv_row["id"]
    else:
        # 既存会話: 指定ID を使用
        conv_id = str(req.conversation_id)
    
    # 2. ユーザーメッセージを保存
    await asyncio.to_thread(
        _insert_message,
        client,
        conv_id,
        "user",           # role: ユーザーメッセージ
        req.message       # content: メッセージ本文
    )
    
    # 3. AI応答を生成
    # (実装例: 単純な返信。実際は OpenAI API など外部サービス使用)
    reply = f"Pythonからの返信: {req.message}"
    
    # 4. AI応答を保存
    await asyncio.to_thread(
        _insert_message,
        client,
        conv_id,
        "bot",            # role: AI応答
        reply             # content: 応答本文
    )
    
    # 5. 会話の最終更新日時を現在時刻に更新
    # (サイドバーの一覧で新順にソートするため)
    await asyncio.to_thread(_touch_conversation, client, conv_id)
    
    # 6. クライアントへ返す
    return ChatResponse(
        reply=reply,
        conversation_id=uuid.UUID(conv_id)
    )
```

---

## 🧪 デバッグのコツ

### ブラウザコンソールで確認

```javascript
// グローバル状態確認
console.log("状態:", { isSendingMessage, isInChatMode, currentConversationId });

// DOM 要素確認
console.log("refs:", refs);

// API レスポンス確認
fetch("/api/conversations")
  .then(r => r.json())
  .then(data => console.log("会話一覧:", data));
```

### API レスポンスの検査

ブラウザの**開発者ツール** → **Network** タブ:
1. `/api/chat` リクエストをクリック
2. **Request** タブ: 送信されたメッセージを確認
3. **Response** タブ: AI応答と会話ID を確認
4. HTTP ステータスコード: 200 (成功) か 500 (エラー) か

### よくあるエラー

| エラー | 原因 | 対策 |
|-------|------|------|
| "会話の読み込みに失敗" | Supabase 接続失敗 | 環境変数確認 |
| 送信ボタンが反応しない | イベントリスナー未登録 | `attachEventListeners()` 実行確認 |
| メッセージが表示されない | DOM 参照が null | `buildPage()` 実行確認 |
| API 415 エラー | Content-Type が違う | `"Content-Type": "application/json"` 確認 |

---

## 📊 パフォーマンス最適化

### 現在の設計

- **DOM キャッシング**: 頻繁にアクセスする要素を `refs` に保存
- **イベント委譲**: `.chip` クリックは document レベルで一元管理
- **API キャッシング**: 初期読み込み時のみ会話一覧取得（新規追加時は prepend）

### 改善検討項目

- [ ] メッセージリストの仮想スクロール（大量メッセージ時）
- [ ] API レスポンスのキャッシング（Redux など状態管理ライブラリ）
- [ ] 画像圧縮・遅延読み込み
- [ ] Web Worker で API 通信を非同期化

---

**文書作成日**: 2026年5月2日
