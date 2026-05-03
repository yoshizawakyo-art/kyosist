import { buildElement, buildInputBox } from "../common/kyouUtils.js";
import {
  buildSidebar,
  loadConversationsIntoSidebar,
  prependConversationItem,
} from "../common/kyouCommon.js";

const CHAT_API_ENDPOINT = "/api/chat";

let isSendingMessage      = false;
let isInChatMode          = false;
let currentConversationId = null;
const refs                = {};

// ── ウェルカム画面の構築 ──

/**
 * 初期表示されるウェルカム画面のDOM構造を生成して返す。
 * テキスト入力欄・送信ボタン・提案チップを含む。
 * 入力欄・送信ボタンへの参照は refs に格納される。
 *
 * @returns {HTMLElement} id="welcome" のセクション要素
 */
function buildWelcomeScreen() {
  const welcomeSection = buildElement("div", null, { id: "welcome" });

  const eyebrowLabel = buildElement("span", "welcome-eyebrow");
  eyebrowLabel.textContent = "kyosist AI";

  const heading = buildElement("h1", "welcome-heading");
  heading.innerHTML = "さあ、今日も<br>一緒に取り組みましょう。";

  const { box, textarea, button } = buildInputBox(
    "welcome-input", "welcome-send",
    "タスクや質問をどうぞ…"
  );
  refs.welcomeInput = textarea;
  refs.welcomeSend  = button;

  const SUGGESTION_CHIPS = [
    { label: "💻 コードを書く",  text: "コードを書いてほしい" },
    { label: "📄 要約する",       text: "この文章を要約してほしい" },
    { label: "💡 アイデア出し",   text: "アイデアを出してほしい" },
    { label: "🌏 翻訳する",       text: "日本語に翻訳してほしい" },
    { label: "🐛 デバッグ",       text: "バグの原因を調べてほしい" },
    { label: "🔍 AIニュース調査", text: "最新のAIニュースを調べてNotionに保存して" },
  ];
  const chipsContainer = buildElement("div", "chips");
  SUGGESTION_CHIPS.forEach(function renderSuggestionChip({ label, text }) {
    const chipElement = buildElement("span", "chip");
    chipElement.textContent = label;
    chipElement.dataset.text = text;
    chipsContainer.appendChild(chipElement);
  });

  welcomeSection.append(eyebrowLabel, heading, box, chipsContainer);
  return welcomeSection;
}

// ── チャット画面の構築 ──

/**
 * メッセージ一覧を表示するチャット画面のDOM構造を生成して返す。
 * メッセージ表示領域への参照は refs.messages に格納される。
 *
 * @returns {HTMLElement} id="chat-view" のコンテナ要素
 */
function buildChatView() {
  const chatViewElement = buildElement("div", null, { id: "chat-view" });
  refs.messages = buildElement("div", null, { id: "messages" });
  chatViewElement.appendChild(refs.messages);
  return chatViewElement;
}

/**
 * チャット画面下部に固定表示されるメッセージ入力バーを生成して返す。
 * 入力欄・送信ボタンへの参照は refs に格納される。
 *
 * @returns {HTMLElement} id="bottom-bar" のコンテナ要素
 */
function buildBottomInputBar() {
  const bottomBarContainer = buildElement("div", null, { id: "bottom-bar" });
  const { box, textarea, button } = buildInputBox(
    "chat-input", "chat-send",
    "メッセージを入力… (Shift+Enter で改行)",
    "bottom-box"
  );
  refs.chatInput = textarea;
  refs.chatSend  = button;
  bottomBarContainer.appendChild(box);
  return bottomBarContainer;
}

/**
 * サイドバー・ウェルカム画面・チャット画面・入力バーをDOMに挿入してページ全体を組み立てる。
 */
function buildPage() {
  const mainElement = buildElement("main", null, { id: "main" });
  refs.welcome   = buildWelcomeScreen();
  refs.chatView  = buildChatView();
  refs.bottomBar = buildBottomInputBar();
  mainElement.append(refs.welcome, refs.chatView, refs.bottomBar);
  document.body.append(buildSidebar(refs), mainElement);
}

// ── テキストエリアのリサイズ ──

/**
 * テキストエリアの高さを入力内容に合わせて自動調整する。
 * 一度 "auto" にリセットしてから scrollHeight で再設定することで縮小にも対応する。
 *
 * @param {HTMLTextAreaElement} textarea - 高さを調整するテキストエリア要素
 */
function resizeTextareaHeight(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = textarea.scrollHeight + "px";
}

// ── メッセージの描画 ──

/**
 * 指定したテキストと送信者ロールのメッセージバブルをチャット画面に追記する。
 * 追記後は自動的に最下部までスクロールする。
 *
 * @param {string} messageText - 表示するメッセージ本文
 * @param {"user"|"bot"} senderRole - 送信者の種別。"user" または "bot"
 */
function appendChatMessage(messageText, senderRole) {
  const messageRow    = buildElement("div", `msg-row ${senderRole}`);
  const avatarElement = buildElement("div", "avatar");
  avatarElement.textContent = senderRole === "user" ? "U" : "K";
  const bubbleElement = buildElement("div", "bubble");
  bubbleElement.textContent = messageText;
  messageRow.append(avatarElement, bubbleElement);
  refs.messages.appendChild(messageRow);
  refs.messages.scrollTop = refs.messages.scrollHeight;
}

/**
 * AIが応答を生成中であることを示すタイピングインジケーターをチャット画面に表示する。
 * 表示した要素は id="typing-row" で識別できる。
 */
function showTypingIndicator() {
  const typingRow     = buildElement("div", "msg-row bot");
  typingRow.id = "typing-row";
  const avatarElement = buildElement("div", "avatar");
  avatarElement.textContent = "K";
  const bubbleElement = buildElement("div", "bubble");
  bubbleElement.innerHTML = `<div class="typing-dots"><span></span><span></span><span></span></div>`;
  typingRow.append(avatarElement, bubbleElement);
  refs.messages.appendChild(typingRow);
  refs.messages.scrollTop = refs.messages.scrollHeight;
}

/**
 * タイピングインジケーターをDOMから除去する。
 * AIの応答が届いたタイミングで呼ぶ。
 */
function hideTypingIndicator() {
  document.getElementById("typing-row")?.remove();
}

// ── 画面状態の切り替え ──

/**
 * ウェルカム画面を非表示にし、チャット画面と入力バーを表示するチャットモードに切り替える。
 */
function enterChatMode() {
  isInChatMode = true;
  refs.welcome.classList.add("hidden");
  refs.chatView.classList.add("visible");
  refs.bottomBar.classList.add("visible");
}

/**
 * チャットモードを終了し、ウェルカム画面に戻す。
 * メッセージ一覧・入力欄・会話IDをリセットする。
 * すでにウェルカム画面表示中の場合は何もしない。
 */
function resetToWelcomeScreen() {
  if (!isInChatMode) return;
  isInChatMode = false;
  currentConversationId = null;
  refs.chatView.classList.remove("visible");
  refs.bottomBar.classList.remove("visible");
  refs.welcome.classList.remove("hidden");
  refs.messages.innerHTML = "";
  refs.chatInput.value = "";
  refs.welcomeInput.value = "";
  resizeTextareaHeight(refs.welcomeInput);
  refs.welcomeInput.focus();
}

// ── 会話履歴の読み込み ──

/**
 * 指定した会話IDの過去メッセージをAPIから取得してチャット画面に描画する。
 * チャットモードでない場合は自動的に切り替える。
 *
 * @param {string} conversationId - 読み込む会話のID
 */
async function loadConversationMessages(conversationId) {
  currentConversationId = conversationId;

  if (!isInChatMode) {
    enterChatMode();
  }

  refs.messages.innerHTML = "";

  try {
    const response = await fetch(`/api/conversations/${conversationId}/messages`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const messages = await response.json();
    messages.forEach(function renderHistoryMessage(message) {
      appendChatMessage(message.content, message.role);
    });
  } catch (err) {
    appendChatMessage(`会話の読み込みに失敗しました: ${err.message}`, "bot");
  }
}

// ── エージェントモード ──

const AGENT_KEYWORDS = ["調べて", "検索して", "ニュース", "Notionに", "リサーチ", "最新の"];

const AGENT_STEP_CONFIG = {
  thought:     { icon: "💭", label: "思考" },
  action:      { icon: "🔧", label: "ツール実行" },
  observation: { icon: "👁", label: "結果取得" },
  error:       { icon: "❌", label: "エラー" },
};

/**
 * メッセージにエージェントキーワードが含まれるか判定する。
 *
 * @param {string} message
 * @returns {boolean}
 */
function shouldUseAgentMode(message) {
  return AGENT_KEYWORDS.some(function containsKeyword(kw) {
    return message.includes(kw);
  });
}

/**
 * エージェントの思考プロセスを表示するコンテナ要素を構築して返す。
 * トグルボタンで展開/折りたたみが可能。
 *
 * @returns {HTMLElement}
 */
function buildAgentProcessContainer() {
  const container = buildElement("div", "agent-process");

  const toggle = buildElement("button", "agent-process-toggle");
  toggle.type = "button";
  const arrowSpan = buildElement("span", "toggle-arrow");
  arrowSpan.textContent = "▾";
  const labelSpan = buildElement("span", "toggle-label");
  labelSpan.textContent = "思考プロセス（実行中...）";
  toggle.append(arrowSpan, labelSpan);

  const stepsDiv = buildElement("div", "agent-steps");

  toggle.addEventListener("click", function onToggleClick() {
    const isHidden = stepsDiv.classList.contains("hidden");
    stepsDiv.classList.toggle("hidden", !isHidden);
    toggle.classList.toggle("collapsed", !isHidden);
  });

  container.append(toggle, stepsDiv);
  return container;
}

/**
 * エージェントのステップをコンテナに追加してトグルラベルを更新する。
 *
 * @param {HTMLElement} container - buildAgentProcessContainer() の戻り値
 * @param {{ type: string, content: string }} step - SSE で受け取ったステップ
 */
function appendAgentStep(container, step) {
  const stepsDiv = container.querySelector(".agent-steps");
  const config = AGENT_STEP_CONFIG[step.type] || { icon: "•", label: step.type };

  const stepEl = buildElement("div", `agent-step ${step.type}`);

  const iconEl = buildElement("span", "step-icon");
  iconEl.textContent = config.icon;

  const bodyEl = buildElement("div", "step-body");

  const labelEl = buildElement("span", "step-label");
  labelEl.textContent = config.label;

  const contentEl = buildElement("p", "step-content");
  contentEl.textContent = step.content;

  bodyEl.append(labelEl, contentEl);
  stepEl.append(iconEl, bodyEl);
  stepsDiv.appendChild(stepEl);

  const toggleLabel = container.querySelector(".toggle-label");
  if (toggleLabel) {
    toggleLabel.textContent = `思考プロセス（${stepsDiv.children.length} ステップ）`;
  }
}

/**
 * エージェントモードでメッセージを送信する。
 * /api/agent/chat に POST して SSE ストリームを読み取り、
 * 思考ステップをリアルタイムで表示し、最終回答をチャットに追加する。
 *
 * @param {string} messageText
 */
async function sendAgentMessage(messageText) {
  isSendingMessage = true;
  refs.welcomeSend.disabled = true;
  refs.chatSend.disabled = true;

  const processContainer = buildAgentProcessContainer();
  refs.messages.appendChild(processContainer);
  refs.messages.scrollTop = refs.messages.scrollHeight;

  const isNewConversation = currentConversationId === null;

  try {
    const response = await fetch("/api/agent/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: messageText,
        conversation_id: currentConversationId,
      }),
    });

    if (!response.ok) {
      const errText = await response.text().catch(function getStatus() { return response.statusText; });
      throw new Error(`HTTP ${response.status}: ${errText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let sidebarAdded = false;
    let isDone = false;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const raw = line.slice(6).trim();
        if (raw === "[DONE]") {
          isDone = true;
          break;
        }

        let step;
        try {
          step = JSON.parse(raw);
        } catch {
          continue;
        }

        if (!sidebarAdded && step.conversation_id) {
          currentConversationId = step.conversation_id;
          if (isNewConversation) {
            prependConversationItem(
              refs.chatHistory,
              { id: step.conversation_id, title: messageText },
              loadConversationMessages
            );
          }
          sidebarAdded = true;
        }

        if (step.type === "answer") {
          appendChatMessage(step.content, "bot");
        } else if (step.type === "error") {
          appendChatMessage(`エージェントエラー: ${step.content}`, "bot");
        } else {
          appendAgentStep(processContainer, step);
        }

        refs.messages.scrollTop = refs.messages.scrollHeight;
      }
      if (isDone) break;
    }
  } catch (err) {
    appendChatMessage(`エラー: ${err.message}`, "bot");
  } finally {
    isSendingMessage = false;
    refs.welcomeSend.disabled = false;
    refs.chatSend.disabled = false;
    refs.chatInput.focus();
  }
}

// ── APIへのメッセージ送信 ──

/**
 * 入力テキストをチャットAPIに送信し、AIの返答をチャット画面に表示する。
 * 送信中は送信ボタンを無効化してタイピングインジケーターを表示する。
 * 新規会話の場合はサイドバー先頭にも会話を追加する。
 *
 * @param {string} messageText - 送信するメッセージ本文
 */
async function sendMessageToAPI(messageText) {
  if (shouldUseAgentMode(messageText)) {
    await sendAgentMessage(messageText);
    return;
  }

  isSendingMessage = true;
  refs.welcomeSend.disabled = true;
  refs.chatSend.disabled    = true;
  showTypingIndicator();

  const isNewConversation = currentConversationId === null;

  try {
    const response = await fetch(CHAT_API_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: messageText,
        conversation_id: currentConversationId,
      }),
    });
    if (!response.ok) {
      function getFallbackErrorText() {
        return response.statusText;
      }
      const errorText = await response.text().catch(getFallbackErrorText);
      throw new Error(`HTTP ${response.status} ${response.statusText}: ${errorText}`);
    }
    const responseData = await response.json();

    currentConversationId = responseData.conversation_id;

    if (isNewConversation) {
      prependConversationItem(
        refs.chatHistory,
        { id: responseData.conversation_id, title: messageText },
        loadConversationMessages
      );
    }

    hideTypingIndicator();
    appendChatMessage(responseData.reply, "bot");
  } catch (err) {
    hideTypingIndicator();
    appendChatMessage(`エラー: ${err.message}`, "bot");
  } finally {
    isSendingMessage = false;
    refs.welcomeSend.disabled = false;
    refs.chatSend.disabled    = false;
    refs.chatInput.focus();
  }
}

// ── 送信処理 ──

/**
 * ウェルカム画面の入力欄からメッセージを送信する。
 * 送信中・空文字の場合は何もしない。
 * 送信後はチャットモードに切り替えてユーザーメッセージを表示する。
 */
function sendFromWelcomeScreen() {
  const messageText = refs.welcomeInput.value.trim();
  if (!messageText || isSendingMessage) return;
  refs.welcomeInput.value = "";
  resizeTextareaHeight(refs.welcomeInput);
  enterChatMode();
  appendChatMessage(messageText, "user");
  sendMessageToAPI(messageText);
}

/**
 * チャット画面下部の入力バーからメッセージを送信する。
 * 送信中・空文字の場合は何もしない。
 */
function sendFromChatInputBar() {
  const messageText = refs.chatInput.value.trim();
  if (!messageText || isSendingMessage) return;
  refs.chatInput.value = "";
  resizeTextareaHeight(refs.chatInput);
  appendChatMessage(messageText, "user");
  sendMessageToAPI(messageText);
}

// ── イベントハンドラ ──

function onWelcomeInputChange() {
  resizeTextareaHeight(refs.welcomeInput);
}

function onWelcomeInputKeydown(e) {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    sendFromWelcomeScreen();
  }
}

function onChatInputChange() {
  resizeTextareaHeight(refs.chatInput);
}

function onChatInputKeydown(e) {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    sendFromChatInputBar();
  }
}

/**
 * チップ（提案ボタン）がクリックされたとき、紐付いたテキストを入力欄にセットする。
 *
 * @param {MouseEvent} e - クリックイベント
 */
function onSuggestionChipClick(e) {
  if (e.target.matches(".chip")) {
    refs.welcomeInput.value = e.target.dataset.text;
    resizeTextareaHeight(refs.welcomeInput);
    refs.welcomeInput.focus();
  }
}

/**
 * 各UI要素にイベントリスナーをアタッチする。
 */
function attachEventListeners() {
  refs.welcomeSend.addEventListener("click", sendFromWelcomeScreen);
  refs.chatSend.addEventListener("click", sendFromChatInputBar);
  refs.newChatBtn.addEventListener("click", resetToWelcomeScreen);

  refs.welcomeInput.addEventListener("input", onWelcomeInputChange);
  refs.welcomeInput.addEventListener("keydown", onWelcomeInputKeydown);

  refs.chatInput.addEventListener("input", onChatInputChange);
  refs.chatInput.addEventListener("keydown", onChatInputKeydown);

  document.addEventListener("click", onSuggestionChipClick);
}

// ── 初期化 ──
buildPage();
attachEventListeners();
loadConversationsIntoSidebar(refs.chatHistory, loadConversationMessages);