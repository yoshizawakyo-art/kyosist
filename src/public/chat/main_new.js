/**
 * =============================================================================
 * Kyosist AI チャットシステム - フロントエンド UI 実装
 * =============================================================================
 *
 * 【概要】
 * このモジュールは kyosist AI チャットシステムのメインUI実装です。
 * ユーザーとの対話インターフェースを提供し、メッセージの送受信、
 * 会話履歴の管理、画面状態の遷移などを制御します。
 *
 * 【主な機能】
 *   ✓ ウェルカム画面の表示と管理
 *   ✓ チャット画面でのメッセージ送受信
 *   ✓ サイドバーから過去会話の読み込み
 *   ✓ テキストエリアの自動高さ調整
 *   ✓ AI応答のタイピングインジケーター表示
 *
 * 【使用方法】
 *   mainScreen.buildPage();
 *   mainScreen.attachEventListeners();
 *   mainScreen.loadConversationsIntoSidebar();
 */

import { uiBuilder } from "../common/kyouUtils.js";
import { sidebarManager } from "../common/kyouCommon.js";

/**
 * ═══════════════════════════════════════════════════════════════════════════
 * メインスクリーン画面管理オブジェクト
 * ═══════════════════════════════════════════════════════════════════════════
 * チャットUI全体のロジック・イベント処理・状態管理を集約したメインオブジェクト
 * 外部から呼び出す際は mainScreen.メソッド名() の形式で使用
 * 例: mainScreen.buildPage()
 */
const mainScreen = {
  // ─────────────────────────────────────────────────────────────────────────
  // グローバル状態変数
  // ─────────────────────────────────────────────────────────────────────────
  
  // 現在の UI状態を追跡する
  isSendingMessage: false,         // API呼び出し中フラグ（重複送信防止用）
  isInChatMode: false,             // チャットモード表示中フラグ
  currentConversationId: null,     // 現在の会話ID（null=新規作成予定）
  refs: {},                        // DOM要素への参照を保持
  
  // Backend API エンドポイント URL
  CHAT_API_ENDPOINT: "/api/chat",

  // ─────────────────────────────────────────────────────────────────────────
  // 【DOM構築セクション】 ウェルカム画面・チャット画面の構築
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * 初期表示されるウェルカム画面のDOM構造を生成して返す。
   * テキスト入力欄・送信ボタン・提案チップを含む。
   * 入力欄・送信ボタンへの参照は this.refs に格納される。
   *
   * @returns {HTMLElement} id="welcome" のセクション要素
   */
  buildWelcomeScreen() {
    const welcomeSection = uiBuilder.buildElement("div", null, { id: "welcome" });

    const eyebrowLabel = uiBuilder.buildElement("span", "welcome-eyebrow");
    eyebrowLabel.textContent = "kyosist AI";

    const heading = uiBuilder.buildElement("h1", "welcome-heading");
    heading.innerHTML = "さあ、今日も<br>一緒に取り組みましょう。";

    const { box, textarea, button } = uiBuilder.buildInputBox(
      "welcome-input", "welcome-send",
      "タスクや質問をどうぞ…"
    );
    this.refs.welcomeInput = textarea;
    this.refs.welcomeSend  = button;

    const SUGGESTION_CHIPS = [
      { label: "💻 コードを書く",  text: "コードを書いてほしい" },
      { label: "📄 要約する",       text: "この文章を要約してほしい" },
      { label: "💡 アイデア出し",   text: "アイデアを出してほしい" },
      { label: "🌏 翻訳する",       text: "日本語に翻訳してほしい" },
      { label: "🐛 デバッグ",       text: "バグの原因を調べてほしい" },
    ];
    const chipsContainer = uiBuilder.buildElement("div", "chips");
    SUGGESTION_CHIPS.forEach(({ label, text }) => {
      const chipElement = uiBuilder.buildElement("span", "chip");
      chipElement.textContent = label;
      chipElement.dataset.text = text;
      chipsContainer.appendChild(chipElement);
    });

    welcomeSection.append(eyebrowLabel, heading, box, chipsContainer);
    return welcomeSection;
  },

  /**
   * メッセージ一覧を表示するチャット画面のDOM構造を生成して返す。
   * メッセージ表示領域への参照は this.refs.messages に格納される。
   *
   * @returns {HTMLElement} id="chat-view" のコンテナ要素
   */
  buildChatView() {
    const chatViewElement = uiBuilder.buildElement("div", null, { id: "chat-view" });
    this.refs.messages = uiBuilder.buildElement("div", null, { id: "messages" });
    chatViewElement.appendChild(this.refs.messages);
    return chatViewElement;
  },

  /**
   * チャット画面下部に固定表示されるメッセージ入力バーを生成して返す。
   * 入力欄・送信ボタンへの参照は this.refs に格納される。
   *
   * @returns {HTMLElement} id="bottom-bar" のコンテナ要素
   */
  buildBottomInputBar() {
    const bottomBarContainer = uiBuilder.buildElement("div", null, { id: "bottom-bar" });
    const { box, textarea, button } = uiBuilder.buildInputBox(
      "chat-input", "chat-send",
      "メッセージを入力… (Shift+Enter で改行)",
      "bottom-box"
    );
    this.refs.chatInput = textarea;
    this.refs.chatSend  = button;
    bottomBarContainer.appendChild(box);
    return bottomBarContainer;
  },

  /**
   * サイドバー・ウェルカム画面・チャット画面・入力バーをDOMに挿入してページ全体を組み立てる。
   * この関数は mainScreen.buildPage() で呼び出すこと
   *
   * @returns {void}
   */
  buildPage() {
    const mainElement = uiBuilder.buildElement("main", null, { id: "main" });
    this.refs.welcome   = this.buildWelcomeScreen();
    this.refs.chatView  = this.buildChatView();
    this.refs.bottomBar = this.buildBottomInputBar();
    mainElement.append(this.refs.welcome, this.refs.chatView, this.refs.bottomBar);
    document.body.append(sidebarManager.buildSidebar(this.refs), mainElement);
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 【UI更新セクション】 テキスト描画・タイピング表示・画面切り替え
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * テキストエリアの高さを入力内容に合わせて自動調整する。
   * 一度 "auto" にリセットしてから scrollHeight で再設定することで縮小にも対応する。
   *
   * @param {HTMLTextAreaElement} textarea - 高さを調整するテキストエリア要素
   */
  resizeTextareaHeight(textarea) {
    textarea.style.height = "auto";
    textarea.style.height = textarea.scrollHeight + "px";
  },

  /**
   * 指定したテキストと送信者ロールのメッセージバブルをチャット画面に追記する。
   * 追記後は自動的に最下部までスクロールする。
   *
   * @param {string} messageText - 表示するメッセージ本文
   * @param {"user"|"bot"} senderRole - 送信者の種別。"user" または "bot"
   */
  appendChatMessage(messageText, senderRole) {
    const messageRow    = uiBuilder.buildElement("div", `msg-row ${senderRole}`);
    const avatarElement = uiBuilder.buildElement("div", "avatar");
    avatarElement.textContent = senderRole === "user" ? "U" : "K";
    const bubbleElement = uiBuilder.buildElement("div", "bubble");
    bubbleElement.textContent = messageText;
    messageRow.append(avatarElement, bubbleElement);
    this.refs.messages.appendChild(messageRow);
    this.refs.messages.scrollTop = this.refs.messages.scrollHeight;
  },

  /**
   * AIが応答を生成中であることを示すタイピングインジケーターをチャット画面に表示する。
   * 表示した要素は id="typing-row" で識別できる。
   */
  showTypingIndicator() {
    const typingRow     = uiBuilder.buildElement("div", "msg-row bot");
    typingRow.id = "typing-row";
    const avatarElement = uiBuilder.buildElement("div", "avatar");
    avatarElement.textContent = "K";
    const bubbleElement = uiBuilder.buildElement("div", "bubble");
    bubbleElement.innerHTML = `<div class="typing-dots"><span></span><span></span><span></span></div>`;
    typingRow.append(avatarElement, bubbleElement);
    this.refs.messages.appendChild(typingRow);
    this.refs.messages.scrollTop = this.refs.messages.scrollHeight;
  },

  /**
   * タイピングインジケーターをDOMから除去する。
   * AIの応答が届いたタイミングで呼ぶ。
   */
  hideTypingIndicator() {
    document.getElementById("typing-row")?.remove();
  },

  /**
   * ウェルカム画面を非表示にし、チャット画面と入力バーを表示するチャットモードに切り替える。
   */
  enterChatMode() {
    this.isInChatMode = true;
    this.refs.welcome.classList.add("hidden");
    this.refs.chatView.classList.add("visible");
    this.refs.bottomBar.classList.add("visible");
  },

  /**
   * チャットモードを終了し、ウェルカム画面に戻す。
   * メッセージ一覧・入力欄・会話IDをリセットする。
   * すでにウェルカム画面表示中の場合は何もしない。
   */
  resetToWelcomeScreen() {
    if (!this.isInChatMode) return;
    this.isInChatMode = false;
    this.currentConversationId = null;
    this.refs.chatView.classList.remove("visible");
    this.refs.bottomBar.classList.remove("visible");
    this.refs.welcome.classList.remove("hidden");
    this.refs.messages.innerHTML = "";
    this.refs.chatInput.value = "";
    this.refs.welcomeInput.value = "";
    this.resizeTextareaHeight(this.refs.welcomeInput);
    this.refs.welcomeInput.focus();
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 【API通信セクション】 メッセージ送信・会話読み込み
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * 指定した会話IDの過去メッセージをAPIから取得してチャット画面に描画する。
   * チャットモードでない場合は自動的に切り替える。
   *
   * @param {string} conversationId - 読み込む会話のID
   */
  async loadConversationMessages(conversationId) {
    this.currentConversationId = conversationId;

    if (!this.isInChatMode) {
      this.enterChatMode();
    }

    this.refs.messages.innerHTML = "";

    try {
      const response = await fetch(`/api/conversations/${conversationId}/messages`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const messages = await response.json();
      messages.forEach((message) => {
        this.appendChatMessage(message.content, message.role);
      });
    } catch (err) {
      this.appendChatMessage(`会話の読み込みに失敗しました: ${err.message}`, "bot");
    }
  },

  /**
   * 入力テキストをチャットAPIに送信し、AIの返答をチャット画面に表示する。
   * 送信中は送信ボタンを無効化してタイピングインジケーターを表示する。
   * 新規会話の場合はサイドバー先頭にも会話を追加する。
   *
   * @param {string} messageText - 送信するメッセージ本文
   */
  async sendMessageToAPI(messageText) {
    this.isSendingMessage = true;
    this.refs.welcomeSend.disabled = true;
    this.refs.chatSend.disabled    = true;
    this.showTypingIndicator();

    const isNewConversation = this.currentConversationId === null;

    try {
      const response = await fetch(this.CHAT_API_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: messageText,
          conversation_id: this.currentConversationId,
        }),
      });
      if (!response.ok) {
        const errorText = await response.text().catch(() => response.statusText);
        throw new Error(`HTTP ${response.status} ${response.statusText}: ${errorText}`);
      }
      const responseData = await response.json();

      this.currentConversationId = responseData.conversation_id;

      if (isNewConversation) {
        sidebarManager.prependConversationItem(
          this.refs.chatHistory,
          { id: responseData.conversation_id, title: messageText },
          (id) => this.loadConversationMessages(id)
        );
      }

      this.hideTypingIndicator();
      this.appendChatMessage(responseData.reply, "bot");
    } catch (err) {
      this.hideTypingIndicator();
      this.appendChatMessage(`エラー: ${err.message}`, "bot");
    } finally {
      this.isSendingMessage = false;
      this.refs.welcomeSend.disabled = false;
      this.refs.chatSend.disabled    = false;
      this.refs.chatInput.focus();
    }
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 【送信処理セクション】 ウェルカム画面・チャット画面からのメッセージ送信
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * ウェルカム画面の入力欄からメッセージを送信する。
   * 送信中・空文字の場合は何もしない。
   * 送信後はチャットモードに切り替えてユーザーメッセージを表示する。
   */
  sendFromWelcomeScreen() {
    const messageText = this.refs.welcomeInput.value.trim();
    if (!messageText || this.isSendingMessage) return;
    this.refs.welcomeInput.value = "";
    this.resizeTextareaHeight(this.refs.welcomeInput);
    this.enterChatMode();
    this.appendChatMessage(messageText, "user");
    this.sendMessageToAPI(messageText);
  },

  /**
   * チャット画面下部の入力バーからメッセージを送信する。
   * 送信中・空文字の場合は何もしない。
   */
  sendFromChatInputBar() {
    const messageText = this.refs.chatInput.value.trim();
    if (!messageText || this.isSendingMessage) return;
    this.refs.chatInput.value = "";
    this.resizeTextareaHeight(this.refs.chatInput);
    this.appendChatMessage(messageText, "user");
    this.sendMessageToAPI(messageText);
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 【イベントハンドラセクション】 ユーザー入力処理
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * ウェルカム入力欄の入力イベントハンドラ
   * テキストエリアの高さを自動調整
   */
  onWelcomeInputChange() {
    mainScreen.resizeTextareaHeight(mainScreen.refs.welcomeInput);
  },

  /**
   * ウェルカム入力欄のキー入力イベントハンドラ
   * Enter キー（Shift キーなし）で送信
   */
  onWelcomeInputKeydown(e) {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      mainScreen.sendFromWelcomeScreen();
    }
  },

  /**
   * チャット入力欄の入力イベントハンドラ
   * テキストエリアの高さを自動調整
   */
  onChatInputChange() {
    mainScreen.resizeTextareaHeight(mainScreen.refs.chatInput);
  },

  /**
   * チャット入力欄のキー入力イベントハンドラ
   * Enter キー（Shift キーなし）で送信
   */
  onChatInputKeydown(e) {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      mainScreen.sendFromChatInputBar();
    }
  },

  /**
   * 提案チップ（suggestion chip）クリックハンドラ
   * ウェルカム画面の提案チップクリック時に、テキストを入力欄に自動入力
   *
   * @param {MouseEvent} e - クリックイベント
   */
  onSuggestionChipClick(e) {
    if (e.target.matches(".chip")) {
      mainScreen.refs.welcomeInput.value = e.target.dataset.text;
      mainScreen.resizeTextareaHeight(mainScreen.refs.welcomeInput);
      mainScreen.refs.welcomeInput.focus();
    }
  },

  /**
   * 各UI要素にイベントリスナーをアタッチする。
   * ページ読み込み後に mainScreen.attachEventListeners() で呼び出す
   */
  attachEventListeners() {
    // ━━ 送信ボタンのクリックイベント ━━━━━━━━━━━━━━━━━━━━━━━━━
    this.refs.welcomeSend.addEventListener("click", () => this.sendFromWelcomeScreen());
    this.refs.chatSend.addEventListener("click", () => this.sendFromChatInputBar());
    this.refs.newChatBtn.addEventListener("click", () => this.resetToWelcomeScreen());

    // ━━ テキストエリアのリアルタイム高さ調整 ━━━━━━━━━━━━━━━━
    this.refs.welcomeInput.addEventListener("input", this.onWelcomeInputChange);
    this.refs.welcomeInput.addEventListener("keydown", this.onWelcomeInputKeydown);

    // ━━ チャット入力欄のリアルタイム高さ調整 ━━━━━━━━━━━━━━━━
    this.refs.chatInput.addEventListener("input", this.onChatInputChange);
    this.refs.chatInput.addEventListener("keydown", this.onChatInputKeydown);

    // ━━ 提案チップクリック（イベント委譲） ━━━━━━━━━━━━━━━━━
    document.addEventListener("click", this.onSuggestionChipClick);
  },

  /**
   * 会話一覧をサイドバーに読み込む
   * ページ読み込み後に mainScreen.loadConversationsIntoSidebar() で呼び出す
   */
  async loadConversationsIntoSidebar() {
    await sidebarManager.loadConversationsIntoSidebar(
      this.refs.chatHistory,
      (conversationId) => this.loadConversationMessages(conversationId)
    );
  },
};

// ═══════════════════════════════════════════════════════════════════════════
// ページ初期化処理
// ═══════════════════════════════════════════════════════════════════════════
// 以下の3つの処理は JavaScript モジュール読み込み時に自動実行

// ステップ 1: ページ全体の DOM を構築
mainScreen.buildPage();

// ステップ 2: 各 UI 要素にイベントリスナーを登録
mainScreen.attachEventListeners();

// ステップ 3: 過去会話一覧をサイドバーに読み込む
mainScreen.loadConversationsIntoSidebar();

export { mainScreen };
