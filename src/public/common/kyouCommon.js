import { buildElement, buildSidebarIcon } from "./kyouUtils.js";

const CONVERSATIONS_ENDPOINT = "/api/conversations";

export function getAuthToken() {
  return localStorage.getItem("kyosist_token");
}

export function getAuthHeaders() {
  const token = getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function redirectToLogin() {
  window.location.href = "/auth/login.html";
}

// ─── ID生成 ───────────────────────────────────────────────────

/**
 * テーブル略称と現在日時を組み合わせたプライマリーキーを生成して返す。
 * 生成フォーマット: <テーブル略称3文字><yy><mm><dd><hh><ss>
 * 例: messages テーブル → "msg2605021423"
 *
 * @param {string} tablePrefix - テーブル名の略称（半角英小文字3文字。例: 'msg', 'usr', 'ses'）
 * @returns {string} テーブル略称 + 年(2桁) + 月(2桁) + 日(2桁) + 時(2桁) + 秒(2桁) の文字列
 */
export function generatePrimaryKey(tablePrefix) {
  const now    = new Date();
  const year   = String(now.getFullYear()).slice(-2);
  const month  = String(now.getMonth() + 1).padStart(2, "0");
  const day    = String(now.getDate()).padStart(2, "0");
  const hour   = String(now.getHours()).padStart(2, "0");
  const second = String(now.getSeconds()).padStart(2, "0");
  return tablePrefix + year + month + day + hour + second;
}

// ─── サイドバー ───────────────────────────────────────────────

/**
 * 共通サイドバーのDOM構造を生成し、呼び出し元が参照するノードを refs に格納して返す。
 * イベントのバインドは呼び出し元が担当する（ページによって振る舞いが異なるため）。
 *
 * 呼び出し後に refs に格納されるプロパティ:
 *   refs.newChatBtn   - "新しいチャット" ボタン要素
 *   refs.chatHistory  - 会話履歴リストの親コンテナ要素
 *
 * @param {object} refs - キー要素の参照を格納するオブジェクト（呼び出し元で作成して渡す）
 * @returns {HTMLElement} id="sidebar" のナビゲーション要素
 */
export function buildSidebar(refs) {
  const sidebar = buildElement("nav", null, { id: "sidebar" });

  const logoRow  = buildElement("div", "logo-row");
  const logoMark = buildElement("div", "logo-mark");
  logoMark.textContent = "K";
  const logoText = buildElement("span", "logo-text");
  logoText.textContent = "kyosist";
  logoRow.append(logoMark, logoText);

  const newChatButton = buildElement("button", "sb-btn new");
  newChatButton.append(
    buildSidebarIcon(`<line x1="12" y1="5" x2="12" y2="19"/>
                      <line x1="5" y1="12" x2="19" y2="12"/>`),
    "新しいチャット"
  );
  refs.newChatBtn = newChatButton;

  const searchButton = buildElement("button", "sb-btn");
  searchButton.append(
    buildSidebarIcon(`<circle cx="11" cy="11" r="8"/>
                      <line x1="21" y1="21" x2="16.65" y2="16.65"/>`),
    "検索"
  );

  const historyLabel = buildElement("div", "sb-label");
  historyLabel.textContent = "最近のチャット";

  const historyContainer = buildElement("div", null, { id: "chat-history" });
  refs.chatHistory = historyContainer;

  const skillsButton = buildElement("a", "sb-btn", { href: "/skills/", id: "nav-skills" });
  if (window.location.pathname.startsWith("/skills")) {
    skillsButton.classList.add("active");
  }
  skillsButton.append(
    buildSidebarIcon(`<circle cx="12" cy="12" r="3"/>
                      <path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/>`),
    "スキル管理"
  );

  sidebar.append(
    logoRow,
    newChatButton,
    searchButton,
    historyLabel,
    historyContainer,
    buildElement("div", "sb-spacer"),
    skillsButton
  );

  return sidebar;
}

/**
 * APIから会話一覧を取得し、取得結果をサイドバーの履歴エリアに描画する。
 * 取得失敗時はエラーメッセージを履歴エリアに表示する。
 *
 * @param {HTMLElement} historyContainer - 会話アイテムを挿入する親コンテナ（refs.chatHistory）
 * @param {function} onConversationSelect - 会話アイテムがクリックされたときのコールバック。
 *   引数: (conversationId: string)
 */
export async function loadConversationsIntoSidebar(historyContainer, onConversationSelect) {
  historyContainer.innerHTML = "";
  try {
    const response = await fetch(CONVERSATIONS_ENDPOINT, {
      headers: getAuthHeaders(),
    });
    if (response.status === 401) {
      redirectToLogin();
      throw new Error("Unauthorized");
    }
    if (!response.ok) {
      const errorText = await response.text().catch(() => response.statusText);
      throw new Error(`HTTP ${response.status} ${response.statusText}: ${errorText}`);
    }
    const conversations = await response.json();
    conversations.forEach(function renderConversationItem(conversation) {
      appendConversationItem(historyContainer, conversation, onConversationSelect);
    });
  } catch (err) {
    console.error("Failed to load conversations:", err);
    const errorElement = buildElement("div", "history-error");
    errorElement.textContent = `履歴の読み込みに失敗: ${err.message}`;
    historyContainer.appendChild(errorElement);
  }
}

/**
 * 新規会話アイテムをサイドバー履歴の先頭に追加し、そのアイテムをアクティブ状態にする。
 * 既存のアクティブアイテムはすべて非アクティブに戻す。
 *
 * @param {HTMLElement} historyContainer - 会話アイテムを挿入する親コンテナ（refs.chatHistory）
 * @param {{ id: string, title: string }} conversation - 追加する会話データ
 * @param {function} onConversationSelect - 会話アイテムクリック時のコールバック。
 *   引数: (conversationId: string)
 */
export function prependConversationItem(historyContainer, conversation, onConversationSelect) {
  historyContainer.querySelectorAll(".history-item").forEach(function clearActiveState(item) {
    item.classList.remove("active");
  });
  const conversationItem = buildConversationItemElement(conversation, onConversationSelect);
  conversationItem.classList.add("active");
  historyContainer.prepend(conversationItem);
}

/**
 * 会話1件分のリストアイテム要素を生成して返す。（内部ヘルパー）
 * タイトルが30文字を超える場合は省略して末尾に "…" を付加する。
 *
 * @param {{ id: string, title: string }} conversation - 表示する会話データ
 * @param {function} onConversationSelect - クリック時に呼ぶコールバック。引数: (conversationId: string)
 * @returns {HTMLElement} CSSクラス "history-item" が付いたdiv要素
 */
function buildConversationItemElement(conversation, onConversationSelect) {
  const displayTitle = conversation.title.length > 30
    ? conversation.title.slice(0, 30) + "…"
    : conversation.title;

  const itemElement = document.createElement("div");
  itemElement.className = "history-item";
  itemElement.dataset.conversationId = conversation.id;
  itemElement.innerHTML = `<span class="history-dot"></span>
                           <span class="history-label">${displayTitle}</span>`;

  itemElement.addEventListener("click", function handleConversationItemClick() {
    itemElement.closest("#chat-history")
      .querySelectorAll(".history-item")
      .forEach(function clearActiveState(item) {
        item.classList.remove("active");
      });
    itemElement.classList.add("active");
    onConversationSelect(conversation.id);
  });

  return itemElement;
}

/**
 * 会話アイテム要素を生成してリスト末尾に追加する。（内部ヘルパー）
 *
 * @param {HTMLElement} historyContainer - 追加先の親コンテナ
 * @param {{ id: string, title: string }} conversation - 表示する会話データ
 * @param {function} onConversationSelect - クリック時に呼ぶコールバック。引数: (conversationId: string)
 */
function appendConversationItem(historyContainer, conversation, onConversationSelect) {
  historyContainer.appendChild(buildConversationItemElement(conversation, onConversationSelect));
}
