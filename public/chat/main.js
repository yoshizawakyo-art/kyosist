import { el, buildInputBox } from "../common/dom.js";
import { buildSidebar, addHistoryItem } from "../common/sidebar.js";

const API_URL = "/api/chat";

// ── State ──
let isSending = false;
let inChat    = false;
const refs    = {};

// ── Welcome screen ──
function buildWelcome() {
  const section = el("div", null, { id: "welcome" });

  const eyebrow = el("span", "welcome-eyebrow");
  eyebrow.textContent = "kyosist AI";

  const heading = el("h1", "welcome-heading");
  heading.innerHTML = "さあ、今日も<br>一緒に取り組みましょう。";

  const { box, ta, btn } = buildInputBox(
    "welcome-input", "welcome-send",
    "タスクや質問をどうぞ…"
  );
  refs.welcomeInput = ta;
  refs.welcomeSend  = btn;

  const CHIPS = [
    { label: "💻 コードを書く",  text: "コードを書いてほしい" },
    { label: "📄 要約する",       text: "この文章を要約してほしい" },
    { label: "💡 アイデア出し",   text: "アイデアを出してほしい" },
    { label: "🌏 翻訳する",       text: "日本語に翻訳してほしい" },
    { label: "🐛 デバッグ",       text: "バグの原因を調べてほしい" },
  ];
  const chipsWrap = el("div", "chips");
  CHIPS.forEach(({ label, text }) => {
    const chip = el("span", "chip");
    chip.textContent = label;
    chip.dataset.text = text;
    chipsWrap.appendChild(chip);
  });

  section.append(eyebrow, heading, box, chipsWrap);
  return section;
}

// ── Chat view ──
function buildChatView() {
  const view = el("div", null, { id: "chat-view" });
  refs.messages = el("div", null, { id: "messages" });
  view.appendChild(refs.messages);
  return view;
}

// ── Bottom input bar ──
function buildBottomBar() {
  const bar = el("div", null, { id: "bottom-bar" });
  const { box, ta, btn } = buildInputBox(
    "chat-input", "chat-send",
    "メッセージを入力… (Shift+Enter で改行)",
    "bottom-box"
  );
  refs.chatInput = ta;
  refs.chatSend  = btn;
  bar.appendChild(box);
  return bar;
}

// ── Page assembly ──
function buildPage() {
  const main = el("main", null, { id: "main" });
  refs.welcome   = buildWelcome();
  refs.chatView  = buildChatView();
  refs.bottomBar = buildBottomBar();
  main.append(refs.welcome, refs.chatView, refs.bottomBar);
  document.body.append(buildSidebar(refs), main);
}

// ── Textarea auto-resize ──
function resize(ta) {
  ta.style.height = "auto";
  ta.style.height = ta.scrollHeight + "px";
}

// ── Message rendering ──
function appendMsg(text, role) {
  const row = el("div", `msg-row ${role}`);
  const av  = el("div", "avatar");
  av.textContent = role === "user" ? "U" : "K";
  const bub = el("div", "bubble");
  bub.textContent = text;
  row.append(av, bub);
  refs.messages.appendChild(row);
  refs.messages.scrollTop = refs.messages.scrollHeight;
}

function showTyping() {
  const row = el("div", "msg-row bot");
  row.id = "typing-row";
  const av = el("div", "avatar");
  av.textContent = "K";
  const bub = el("div", "bubble");
  bub.innerHTML = `<div class="typing-dots"><span></span><span></span><span></span></div>`;
  row.append(av, bub);
  refs.messages.appendChild(row);
  refs.messages.scrollTop = refs.messages.scrollHeight;
}

function hideTyping() {
  document.getElementById("typing-row")?.remove();
}

// ── State transitions ──
function enterChatMode(firstMsg) {
  inChat = true;
  refs.welcome.classList.add("hidden");
  refs.chatView.classList.add("visible");
  refs.bottomBar.classList.add("visible");
  addHistoryItem(refs.chatHistory, firstMsg);
}

function resetToWelcome() {
  if (!inChat) return;
  inChat = false;
  refs.chatView.classList.remove("visible");
  refs.bottomBar.classList.remove("visible");
  refs.welcome.classList.remove("hidden");
  refs.messages.innerHTML = "";
  refs.chatInput.value = "";
  refs.welcomeInput.value = "";
  resize(refs.welcomeInput);
  refs.welcomeInput.focus();
}

// ── API ──
async function callAPI(text) {
  isSending = true;
  refs.welcomeSend.disabled = true;
  refs.chatSend.disabled    = true;
  showTyping();

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    hideTyping();
    appendMsg(data.reply, "bot");
  } catch (err) {
    hideTyping();
    appendMsg(`エラー: ${err.message}`, "bot");
  } finally {
    isSending = false;
    refs.welcomeSend.disabled = false;
    refs.chatSend.disabled    = false;
    refs.chatInput.focus();
  }
}

// ── Send handlers ──
function sendFromWelcome() {
  const text = refs.welcomeInput.value.trim();
  if (!text || isSending) return;
  refs.welcomeInput.value = "";
  resize(refs.welcomeInput);
  enterChatMode(text);
  appendMsg(text, "user");
  callAPI(text);
}

function sendFromChat() {
  const text = refs.chatInput.value.trim();
  if (!text || isSending) return;
  refs.chatInput.value = "";
  resize(refs.chatInput);
  appendMsg(text, "user");
  callAPI(text);
}

// ── Events ──
function attachEvents() {
  refs.welcomeSend.addEventListener("click", sendFromWelcome);
  refs.chatSend.addEventListener("click", sendFromChat);
  refs.newChatBtn.addEventListener("click", resetToWelcome);

  refs.welcomeInput.addEventListener("input", () => resize(refs.welcomeInput));
  refs.welcomeInput.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      sendFromWelcome();
    }
  });

  refs.chatInput.addEventListener("input", () => resize(refs.chatInput));
  refs.chatInput.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      sendFromChat();
    }
  });

  // Chip click (delegated to avoid per-element listeners)
  document.addEventListener("click", e => {
    if (e.target.matches(".chip")) {
      refs.welcomeInput.value = e.target.dataset.text;
      resize(refs.welcomeInput);
      refs.welcomeInput.focus();
    }
  });
}

// ── Init ──
buildPage();
attachEvents();
