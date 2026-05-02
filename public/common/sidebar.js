import { el, icon } from "./dom.js";

/**
 * Build the shared sidebar and populate refs with key nodes.
 * Event binding is left to the caller (behaviour differs per page).
 *
 * Populated refs:
 *   refs.newChatBtn   - "新しいチャット" button
 *   refs.chatHistory  - history list container
 *
 * @param {object} refs
 * @returns {HTMLElement}
 */
export function buildSidebar(refs) {
  const sidebar = el("nav", null, { id: "sidebar" });

  // Logo
  const logoRow  = el("div", "logo-row");
  const logoMark = el("div", "logo-mark");
  logoMark.textContent = "K";
  const logoText = el("span", "logo-text");
  logoText.textContent = "kyosist";
  logoRow.append(logoMark, logoText);

  // New chat
  const newBtn = el("button", "sb-btn new");
  newBtn.append(
    icon(`<line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>`),
    "新しいチャット"
  );
  refs.newChatBtn = newBtn;

  // Search
  const searchBtn = el("button", "sb-btn");
  searchBtn.append(
    icon(`<circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>`),
    "検索"
  );

  // History section
  const historyLabel = el("div", "sb-label");
  historyLabel.textContent = "最近のチャット";

  const history = el("div", null, { id: "chat-history" });
  refs.chatHistory = history;

  sidebar.append(
    logoRow,
    newBtn,
    searchBtn,
    historyLabel,
    history,
    el("div", "sb-spacer")
  );

  return sidebar;
}

/**
 * Prepend an item to the chat history list.
 * @param {HTMLElement} historyEl - refs.chatHistory
 * @param {string} label
 */
export function addHistoryItem(historyEl, label) {
  const truncated = label.length > 30 ? label.slice(0, 30) + "…" : label;

  historyEl.querySelectorAll(".history-item").forEach(n => n.classList.remove("active"));

  const item = document.createElement("div");
  item.className = "history-item active";
  item.innerHTML = `<span class="history-dot"></span>
                    <span class="history-label">${truncated}</span>`;
  historyEl.prepend(item);
}
