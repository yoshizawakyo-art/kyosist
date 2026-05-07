/**
 * タスク実行機能（UI統合）
 * - タスク入力フォーム
 * - 実行結果表示
 * - 実行履歴パネル
 */

const TASK_EXECUTOR_API_ENDPOINT = "/api/tasks/execute";
const TASK_HISTORY_API_ENDPOINT = "/api/tasks/history";
const TASK_SKILLS_API_ENDPOINT = "/api/tasks/skills";

let isExecutingTask = false;
let taskHistory = [];
let taskSkills = [];
const taskRefs = {};

/**
 * タスク実行セクションのDOM構造を生成して返す
 * @returns {HTMLElement}
 */
function buildTaskExecutorSection() {
  const taskSection = document.createElement("div");
  taskSection.id = "task-section";
  taskSection.className = "task-section";

  // タイトル
  const heading = document.createElement("h2");
  heading.textContent = "タスク実行";
  taskSection.appendChild(heading);

  // フォーム
  const form = document.createElement("form");
  form.id = "task-form";
  form.className = "task-form";

  // タスク入力テキストエリア
  const inputLabel = document.createElement("label");
  inputLabel.htmlFor = "task-input";
  inputLabel.textContent = "タスク指示:";
  form.appendChild(inputLabel);

  const textarea = document.createElement("textarea");
  textarea.id = "task-input";
  textarea.className = "task-input";
  textarea.placeholder = "例: ファイル /tmp/test.txt を作成して内容: Hello";
  textarea.rows = 4;
  taskRefs.taskInput = textarea;
  form.appendChild(textarea);

  // ボタングループ
  const buttonGroup = document.createElement("div");
  buttonGroup.className = "button-group";

  const executeBtn = document.createElement("button");
  executeBtn.id = "task-execute-btn";
  executeBtn.type = "button";
  executeBtn.className = "btn btn-primary";
  executeBtn.textContent = "実行";
  executeBtn.addEventListener("click", handleTaskExecute);
  taskRefs.executeBtn = executeBtn;
  buttonGroup.appendChild(executeBtn);

  const cancelBtn = document.createElement("button");
  cancelBtn.id = "task-cancel-btn";
  cancelBtn.type = "button";
  cancelBtn.className = "btn btn-secondary";
  cancelBtn.textContent = "キャンセル";
  cancelBtn.addEventListener("click", handleTaskCancel);
  taskRefs.cancelBtn = cancelBtn;
  buttonGroup.appendChild(cancelBtn);

  const saveSkillBtn = document.createElement("button");
  saveSkillBtn.id = "task-save-skill-btn";
  saveSkillBtn.type = "button";
  saveSkillBtn.className = "btn btn-secondary";
  saveSkillBtn.textContent = "スキル保存";
  saveSkillBtn.addEventListener("click", handleSaveSkill);
  buttonGroup.appendChild(saveSkillBtn);

  form.appendChild(buttonGroup);
  taskSection.appendChild(form);

  // 実行結果表示エリア
  const resultContainer = document.createElement("div");
  resultContainer.id = "task-result";
  resultContainer.className = "task-result";
  resultContainer.style.display = "none";

  const resultHeading = document.createElement("h3");
  resultHeading.textContent = "実行結果";
  resultContainer.appendChild(resultHeading);

  const resultContent = document.createElement("div");
  resultContent.id = "result-content";
  resultContent.className = "result-content";
  taskRefs.resultContent = resultContent;
  resultContainer.appendChild(resultContent);

  taskSection.appendChild(resultContainer);

  // 実行履歴パネル
  const historyContainer = document.createElement("div");
  historyContainer.id = "task-history";
  historyContainer.className = "task-history";

  const historyHeading = document.createElement("h3");
  historyHeading.textContent = "実行履歴（最近10件）";
  historyContainer.appendChild(historyHeading);

  const historyList = document.createElement("ul");
  historyList.id = "history-list";
  historyList.className = "history-list";
  taskRefs.historyList = historyList;
  historyContainer.appendChild(historyList);

  taskSection.appendChild(historyContainer);

  const skillContainer = document.createElement("div");
  skillContainer.id = "task-skills";
  skillContainer.className = "task-skills";
  const skillHeading = document.createElement("h3");
  skillHeading.textContent = "保存済みスキル";
  skillContainer.appendChild(skillHeading);
  const skillList = document.createElement("ul");
  skillList.id = "skill-list";
  skillList.className = "history-list";
  taskRefs.skillList = skillList;
  skillContainer.appendChild(skillList);
  taskSection.appendChild(skillContainer);

  loadTaskHistory();
  loadTaskSkills();

  return taskSection;
}

/**
 * タスク実行ボタンのハンドラ
 */
async function handleTaskExecute() {
  const input = taskRefs.taskInput.value.trim();

  if (!input) {
    showTaskResult("エラー", "タスク指示を入力してください", "error");
    return;
  }

  isExecutingTask = true;
  taskRefs.executeBtn.disabled = true;

  // spinner 表示
  showSpinner("実行中...");

  try {
    const response = await fetch(TASK_EXECUTOR_API_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-User-ID": getUserId(),
      },
      body: JSON.stringify({ user_input: input }),
    });

    if (response.status === 401) {
      window.location.href = "/auth/login.html";
      return;
    }

    const result = await response.json();

    if (result.status === "success") {
      showTaskResult("成功", formatResult(result), "success");
      addToHistory({
        id: result.id,
        task_type: result.task_type,
        task_input: input,
        status: result.status,
        created_at: result.created_at,
      });
    } else {
      showTaskResult("エラー", result.result?.message || "実行に失敗しました", "error");
    }
  } catch (error) {
    showTaskResult("エラー", `リクエスト失敗: ${error.message}`, "error");
  } finally {
    isExecutingTask = false;
    taskRefs.executeBtn.disabled = false;
  }
}

/**
 * タスクキャンセルボタンのハンドラ
 */
function handleTaskCancel() {
  taskRefs.taskInput.value = "";
  taskRefs.resultContent.innerHTML = "";
  taskRefs.resultContent.parentElement.style.display = "none";
}

async function handleSaveSkill() {
  const input = taskRefs.taskInput.value.trim();
  if (!input) {
    showTaskResult("エラー", "保存するタスク指示を入力してください", "error");
    return;
  }

  try {
    const response = await fetch(TASK_SKILLS_API_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-User-ID": getUserId(),
      },
      body: JSON.stringify({
        skill_name: input.substring(0, 30),
        description: input,
        pattern: { task_type: "unknown", action: "execute", params: { user_input: input } },
      }),
    });
    const skill = await response.json();
    taskSkills.unshift(skill);
    renderSkills();
    showTaskResult("成功", "スキルを保存しました", "success");
  } catch (error) {
    showTaskResult("エラー", `スキル保存失敗: ${error.message}`, "error");
  }
}

/**
 * 結果を表示
 * @param {string} title
 * @param {string} message
 * @param {string} status - "success" or "error"
 */
function showTaskResult(title, message, status) {
  const resultContainer = taskRefs.resultContent.parentElement;
  resultContainer.style.display = "block";
  resultContainer.className = `task-result ${status}`;

  taskRefs.resultContent.innerHTML = "";
  const item = document.createElement("div");
  item.className = "result-item";
  const heading = document.createElement("h4");
  heading.textContent = title;
  const body = document.createElement("div");
  body.className = "result-body";
  body.appendChild(typeof message === "string" ? document.createTextNode(message) : message);
  item.append(heading, body);
  taskRefs.resultContent.appendChild(item);
}

/**
 * spinner を表示
 */
function showSpinner(message) {
  const resultContainer = taskRefs.resultContent.parentElement;
  resultContainer.style.display = "block";
  resultContainer.className = "task-result loading";

  taskRefs.resultContent.innerHTML = `
    <div class="spinner">
      <div class="spinner-dot"></div>
      <p>${message}</p>
    </div>
  `;
}

/**
 * 履歴に追加
 */
function addToHistory(item) {
  taskHistory.unshift(item);
  // 最大10件に制限
  if (taskHistory.length > 10) {
    taskHistory.pop();
  }
  renderHistory();
}

/**
 * 履歴を描画
 */
function renderHistory() {
  taskRefs.historyList.innerHTML = "";
  taskHistory.forEach((item) => {
    const li = document.createElement("li");
    li.className = `history-item status-${item.status}`;
    li.innerHTML = `
      <div class="history-item-header">
        <span class="history-type">${escapeHtml(item.task_type)}</span>
        <span class="history-status">${item.status}</span>
        <span class="history-time">${formatTime(item.created_at)}</span>
      </div>
      <div class="history-input">${escapeHtml(item.task_input.substring(0, 60))}...</div>
    `;
    li.addEventListener("click", function handleReexecute() {
      taskRefs.taskInput.value = item.task_input;
      taskRefs.taskInput.focus();
    });
    taskRefs.historyList.appendChild(li);
  });
}

function renderSkills() {
  taskRefs.skillList.innerHTML = "";
  taskSkills.forEach((item) => {
    const li = document.createElement("li");
    li.className = "history-item";
    li.innerHTML = `
      <div class="history-item-header">
        <span class="history-type">${escapeHtml(item.skill_name)}</span>
        <span class="history-time">${formatTime(item.created_at)}</span>
      </div>
      <div class="history-input">${escapeHtml(item.description || "")}</div>
    `;
    li.addEventListener("click", function handleSkillReuse() {
      const savedInput = item.pattern?.params?.user_input || item.description || "";
      taskRefs.taskInput.value = savedInput;
      taskRefs.taskInput.focus();
    });
    taskRefs.skillList.appendChild(li);
  });
}

/**
 * 実行結果をフォーマット
 */
function formatResult(result) {
  const payload = result.result || {};
  const wrapper = document.createElement("div");

  if (payload.screenshot) {
    const image = document.createElement("img");
    image.className = "task-screenshot";
    image.alt = "ブラウザ操作スクリーンショット";
    image.src = `data:image/png;base64,${payload.screenshot}`;
    wrapper.appendChild(image);
  }

  if (payload.url) {
    const frame = document.createElement("iframe");
    frame.className = "task-browser-frame";
    frame.src = payload.url;
    frame.title = "ブラウザ操作結果";
    wrapper.appendChild(frame);
  }

  const pre = document.createElement("pre");
  pre.textContent = payload.stdout || payload.message || JSON.stringify(payload, null, 2);
  wrapper.appendChild(pre);
  return wrapper;
}

async function loadTaskHistory() {
  try {
    const response = await fetch(TASK_HISTORY_API_ENDPOINT, {
      headers: { "X-User-ID": getUserId() },
    });
    if (!response.ok) return;
    taskHistory = await response.json();
    renderHistory();
  } catch (_) {
    // 履歴は補助 UI なので初期取得失敗時は空表示のままにする。
  }
}

async function loadTaskSkills() {
  try {
    const response = await fetch(TASK_SKILLS_API_ENDPOINT, {
      headers: { "X-User-ID": getUserId() },
    });
    if (!response.ok) return;
    taskSkills = await response.json();
    renderSkills();
  } catch (_) {
    // スキル一覧も補助 UI のため、失敗時は空表示に留める。
  }
}

/**
 * 時間をフォーマット
 */
function formatTime(isoString) {
  const date = new Date(isoString);
  return date.toLocaleTimeString("ja-JP", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

/**
 * HTML をエスケープ
 */
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

/**
 * ユーザーID を取得（暫定: localStorage から）
 */
function getUserId() {
  return localStorage.getItem("user_id") || "anonymous";
}

// エクスポート
export { buildTaskExecutorSection, taskRefs };
