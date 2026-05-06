import { buildElement } from "../common/kyouUtils.js";
import { buildSidebar } from "../common/kyouCommon.js";

const SKILLS_API = "/api/skills";
const SKILLS_ASSISTANT_API = "/api/skills/assistant";
const AUTOMATION_TASKS_API = "/api/automation/tasks";
const AUTOMATION_RUNS_API = "/api/automation/runs";
const refs = {};
let latestDraft = null;
const assistantHistory = [];

async function loadSkills() {
  try {
    const res = await fetch(SKILLS_API);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const skills = await res.json();
    renderSkillList(skills);
  } catch (err) {
    console.error("スキル取得エラー:", err);
    refs.skillList.innerHTML = `<p class="empty-state">読み込みに失敗しました: ${err.message}</p>`;
  }
}

function renderSkillList(skills) {
  refs.skillList.innerHTML = "";
  if (skills.length === 0) {
    const empty = buildElement("p", "empty-state");
    empty.textContent = "登録されたスキルはありません。";
    refs.skillList.appendChild(empty);
    return;
  }
  skills.forEach(function renderEachSkill(skill) {
    refs.skillList.appendChild(buildSkillCard(skill));
  });
}

function buildSkillCard(skill) {
  const card = buildElement("div", "skill-card");
  const info = buildElement("div", "skill-info");

  const name = buildElement("div", "skill-name");
  name.textContent = skill.name;

  const desc = buildElement("div", "skill-description");
  desc.textContent = skill.description;

  const url = buildElement("div", "skill-url");
  url.textContent = `${skill.action_method} ${skill.action_url}`;

  info.append(name, desc, url);

  const deleteBtn = buildElement("button", "btn-danger");
  deleteBtn.textContent = "削除";
  deleteBtn.addEventListener("click", function onDeleteClick() {
    handleDeleteSkill(skill.id);
  });

  card.append(info, deleteBtn);
  return card;
}

async function handleDeleteSkill(skillId) {
  try {
    const res = await fetch(`${SKILLS_API}/${skillId}`, { method: "DELETE" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    await loadSkills();
  } catch (err) {
    console.error("スキル削除エラー:", err);
  }
}

async function handleFormSubmit(event) {
  event.preventDefault();
  refs.formError.textContent = "";
  refs.submitBtn.disabled = true;

  const name = refs.nameInput.value.trim();
  const description = refs.descInput.value.trim();
  const action_url = refs.urlInput.value.trim();
  const action_method = refs.methodSelect.value;
  const action_body_template = refs.bodyInput.value.trim();

  if (!name || !description || !action_url) {
    refs.formError.textContent = "スキル名・説明・Webhook URL は必須です。";
    refs.submitBtn.disabled = false;
    return;
  }

  try {
    const res = await fetch(SKILLS_API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description, action_url, action_method, action_body_template }),
    });
    if (!res.ok) {
      const errData = await res.json().catch(function returnDefault() { return {}; });
      throw new Error(errData.detail || `HTTP ${res.status}`);
    }
    refs.skillForm.reset();
    await loadSkills();
  } catch (err) {
    console.error("スキル登録エラー:", err);
    refs.formError.textContent = `登録に失敗しました: ${err.message}`;
  } finally {
    refs.submitBtn.disabled = false;
  }
}

function buildAutomationField(labelText, inputElement, hintText = "") {
  const group = buildElement("div", "form-group");
  const label = buildElement("label");
  label.textContent = labelText;
  group.append(label, inputElement);
  if (hintText) {
    const hint = buildElement("p", "form-hint");
    hint.textContent = hintText;
    group.appendChild(hint);
  }
  return group;
}

function buildAutomationToggle(labelText, checkboxElement) {
  const label = buildElement("label", "automation-toggle");
  label.append(checkboxElement, buildElement("span"));
  label.lastChild.textContent = labelText;
  return label;
}

function formatRunStatus(run) {
  return run.status || run.state || "不明";
}

function formatRunTaskName(run) {
  return run.task_name || run.taskName || run.task_id || run.taskId || "未設定";
}

function formatRunTimestamp(run) {
  return run.started_at || run.startedAt || run.created_at || run.createdAt || "-";
}

function formatRunMessage(run) {
  return run.message || run.error || run.log || run.summary || "";
}

function renderAutomationRuns(runs) {
  refs.automationRuns.innerHTML = "";
  if (!Array.isArray(runs) || runs.length === 0) {
    const empty = buildElement("p", "empty-state compact");
    empty.textContent = "実行履歴はまだありません。";
    refs.automationRuns.appendChild(empty);
    return;
  }

  runs.slice(0, 8).forEach(function renderEachRun(run) {
    const row = buildElement("div", "automation-run-row");

    const status = buildElement("span", "automation-run-status");
    status.textContent = formatRunStatus(run);

    const detail = buildElement("div", "automation-run-detail");
    const taskName = buildElement("div", "automation-run-task");
    taskName.textContent = formatRunTaskName(run);
    const meta = buildElement("div", "automation-run-meta");
    meta.textContent = [formatRunTimestamp(run), formatRunMessage(run)].filter(Boolean).join(" / ");
    detail.append(taskName, meta);

    row.append(status, detail);
    refs.automationRuns.appendChild(row);
  });
}

async function loadAutomationRuns() {
  refs.automationRunsError.textContent = "";
  refs.automationRuns.innerHTML = "";
  const loading = buildElement("p", "empty-state compact");
  loading.textContent = "実行履歴を読み込み中です。";
  refs.automationRuns.appendChild(loading);

  try {
    const res = await fetch(AUTOMATION_RUNS_API);
    if (!res.ok) {
      const errData = await res.json().catch(function returnDefault() { return {}; });
      throw new Error(errData.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    renderAutomationRuns(Array.isArray(data) ? data : data.runs);
  } catch (err) {
    console.error("自動化実行履歴取得エラー:", err);
    refs.automationRuns.innerHTML = "";
    refs.automationRunsError.textContent = `実行履歴の読み込みに失敗しました: ${err.message}`;
  }
}

async function handleAutomationTaskSubmit(event) {
  event.preventDefault();
  refs.automationFormError.textContent = "";
  refs.automationFormSuccess.textContent = "";
  refs.automationSubmitBtn.disabled = true;

  const task_name = refs.automationTaskNameInput.value.trim();
  const target_month = refs.automationTargetMonthInput.value;
  const template_path = refs.automationTemplatePathInput.value.trim();
  const output_directory = refs.automationOutputDirectoryInput.value.trim();
  const output_filename_policy = refs.automationFilenamePolicySelect.value;
  const blocked_sites = refs.automationBlockedSitesInput.value
    .split("\n")
    .map(function normalizeSite(site) { return site.trim(); })
    .filter(Boolean);
  const require_login_confirmation = refs.automationLoginConfirmationInput.checked;
  const require_regeneration_approval = refs.automationRegenerationApprovalInput.checked;

  if (!task_name || !target_month || !template_path || !output_directory) {
    refs.automationFormError.textContent = "タスク名・対象月・テンプレートパス・出力先は必須です。";
    refs.automationSubmitBtn.disabled = false;
    return;
  }

  try {
    const res = await fetch(AUTOMATION_TASKS_API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        task_name,
        target_month,
        template_path,
        output_directory,
        output_filename_policy,
        blocked_sites,
        require_login_confirmation,
        require_regeneration_approval,
      }),
    });
    if (!res.ok) {
      const errData = await res.json().catch(function returnDefault() { return {}; });
      throw new Error(errData.detail || `HTTP ${res.status}`);
    }
    refs.automationTaskForm.reset();
    refs.automationLoginConfirmationInput.checked = true;
    refs.automationRegenerationApprovalInput.checked = true;
    refs.automationFormSuccess.textContent = "自動化タスク設定を保存しました。";
    await loadAutomationRuns();
  } catch (err) {
    console.error("自動化タスク保存エラー:", err);
    refs.automationFormError.textContent = `自動化タスク設定の保存に失敗しました: ${err.message}`;
  } finally {
    refs.automationSubmitBtn.disabled = false;
  }
}

function appendAssistantMessage(role, text) {
  const row = buildElement("div", `assistant-message ${role}`);
  row.textContent = text;
  refs.assistantMessages.appendChild(row);
  refs.assistantMessages.scrollTop = refs.assistantMessages.scrollHeight;
}

function applyDraftToForm(draft) {
  refs.nameInput.value = draft.name || "";
  refs.descInput.value = draft.description || "";
  refs.urlInput.value = draft.action_url || "";
  refs.methodSelect.value = draft.action_method || "POST";
  refs.bodyInput.value = draft.action_body_template || "";
}

async function handleAssistantSubmit(event) {
  event.preventDefault();
  const message = refs.assistantInput.value.trim();
  if (!message) return;

  refs.assistantInput.value = "";
  refs.assistantSend.disabled = true;
  refs.assistantError.textContent = "";
  appendAssistantMessage("user", message);
  assistantHistory.push({ role: "user", content: message });

  try {
    const res = await fetch(SKILLS_ASSISTANT_API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history: assistantHistory.slice(-12) }),
    });
    if (!res.ok) {
      const errData = await res.json().catch(function returnDefault() { return {}; });
      throw new Error(errData.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    latestDraft = data.draft || null;
    assistantHistory.push({ role: "assistant", content: data.reply });
    appendAssistantMessage("assistant", data.reply);

    refs.applyDraftBtn.disabled = !latestDraft;
    if (latestDraft) {
      applyDraftToForm(latestDraft);
    }
  } catch (err) {
    refs.assistantError.textContent = `AI対話に失敗しました: ${err.message}`;
  } finally {
    refs.assistantSend.disabled = false;
  }
}

function handleApplyDraft() {
  if (!latestDraft) return;
  applyDraftToForm(latestDraft);
}

function buildAssistantCard() {
  const card = buildElement("div", "assistant-card");
  const title = buildElement("div", "form-section-title");
  title.textContent = "AIと対話してスキル案を作る";

  const description = buildElement("p", "assistant-help");
  description.textContent = "やりたい業務を自然文で入力すると、Webhookスキルの下書きを作成します。";

  const messages = buildElement("div", "assistant-messages");
  refs.assistantMessages = messages;
  appendAssistantMessage("assistant", "まずは「何を自動化したいか」を教えてください。");

  const form = buildElement("form", "assistant-form");
  refs.assistantForm = form;
  const input = buildElement("textarea", "form-textarea", { placeholder: "例: 問い合わせが来たらSlackへ通知して担当者にメンションしたい" });
  refs.assistantInput = input;
  const actions = buildElement("div", "assistant-actions");
  const sendBtn = buildElement("button", "btn-primary", { type: "submit" });
  sendBtn.textContent = "AIに相談";
  refs.assistantSend = sendBtn;
  const applyBtn = buildElement("button", "btn-secondary", { type: "button" });
  applyBtn.textContent = "この案をフォームに反映";
  applyBtn.disabled = true;
  applyBtn.addEventListener("click", handleApplyDraft);
  refs.applyDraftBtn = applyBtn;
  actions.append(sendBtn, applyBtn);

  const error = buildElement("p", "form-error");
  refs.assistantError = error;

  form.append(input, actions, error);
  form.addEventListener("submit", handleAssistantSubmit);

  card.append(title, description, messages, form);
  return card;
}

function buildAutomationSection() {
  const section = buildElement("section", "automation-section");

  const header = buildElement("div", "automation-header");
  const titleBlock = buildElement("div");
  const title = buildElement("div", "form-section-title");
  title.textContent = "業務自動化タスク設定";
  const description = buildElement("p", "automation-help");
  description.textContent = "月次の成果物生成に必要な入力元、出力先、承認ポリシーをまとめて設定します。";
  titleBlock.append(title, description);

  const refreshBtn = buildElement("button", "btn-secondary automation-refresh", { type: "button" });
  refreshBtn.textContent = "履歴を更新";
  refreshBtn.addEventListener("click", loadAutomationRuns);
  header.append(titleBlock, refreshBtn);

  const content = buildElement("div", "automation-content");

  const form = buildElement("form", "automation-form");
  refs.automationTaskForm = form;

  const taskNameInput = buildElement("input", "form-input", {
    type: "text",
    placeholder: "例: 月次作業実績表Excel生成",
    required: "",
  });
  refs.automationTaskNameInput = taskNameInput;

  const targetMonthInput = buildElement("input", "form-input", { type: "month", required: "" });
  refs.automationTargetMonthInput = targetMonthInput;

  const templatePathInput = buildElement("input", "form-input", {
    type: "text",
    placeholder: ".agents/doc/other/作業実績表_吉沢協助_2026mm.xlsx",
    required: "",
  });
  refs.automationTemplatePathInput = templatePathInput;

  const outputDirectoryInput = buildElement("input", "form-input", {
    type: "text",
    placeholder: "例: C:/Users/you/Documents/reports",
    required: "",
  });
  refs.automationOutputDirectoryInput = outputDirectoryInput;

  const filenamePolicySelect = buildElement("select", "form-select");
  [
    ["template_month", "テンプレート形式 + 対象月"],
    ["confirm_each_time", "実行時に確認"],
    ["task_month_timestamp", "タスク名 + 対象月 + 実行日時"],
  ].forEach(function appendFilenamePolicy(option) {
    const optionElement = buildElement("option", null, { value: option[0] });
    optionElement.textContent = option[1];
    filenamePolicySelect.appendChild(optionElement);
  });
  refs.automationFilenamePolicySelect = filenamePolicySelect;

  const blockedSitesInput = buildElement("textarea", "form-textarea automation-sites-input", {
    placeholder: "例:\nhttps://example.com\nhttps://admin.example.com",
  });
  refs.automationBlockedSitesInput = blockedSitesInput;

  const loginConfirmationInput = buildElement("input", null, { type: "checkbox" });
  loginConfirmationInput.checked = true;
  refs.automationLoginConfirmationInput = loginConfirmationInput;

  const regenerationApprovalInput = buildElement("input", null, { type: "checkbox" });
  regenerationApprovalInput.checked = true;
  refs.automationRegenerationApprovalInput = regenerationApprovalInput;

  const fieldGrid = buildElement("div", "automation-field-grid");
  fieldGrid.append(
    buildAutomationField("タスク名", taskNameInput),
    buildAutomationField("対象月", targetMonthInput),
    buildAutomationField("テンプレートパス", templatePathInput),
    buildAutomationField("出力先", outputDirectoryInput),
    buildAutomationField("出力ファイル名ポリシー", filenamePolicySelect),
    buildAutomationField("禁止サイト", blockedSitesInput, "1行に1サイトずつ入力します。")
  );

  const policyRow = buildElement("div", "automation-policy-row");
  policyRow.append(
    buildAutomationToggle("ログイン前後に確認する", loginConfirmationInput),
    buildAutomationToggle("同月再生成時は明示承認を必須にする", regenerationApprovalInput)
  );

  const formActions = buildElement("div", "automation-actions");
  const formError = buildElement("p", "form-error");
  refs.automationFormError = formError;
  const formSuccess = buildElement("p", "form-success");
  refs.automationFormSuccess = formSuccess;
  const submitBtn = buildElement("button", "btn-primary", { type: "submit" });
  submitBtn.textContent = "タスク設定を保存";
  refs.automationSubmitBtn = submitBtn;
  formActions.append(submitBtn, formSuccess);

  form.append(fieldGrid, policyRow, formError, formActions);
  form.addEventListener("submit", handleAutomationTaskSubmit);

  const runsPanel = buildElement("div", "automation-runs-panel");
  const runsTitle = buildElement("div", "automation-runs-title");
  runsTitle.textContent = "実行履歴 / ログ";
  const runs = buildElement("div", "automation-runs");
  refs.automationRuns = runs;
  const runsError = buildElement("p", "form-error");
  refs.automationRunsError = runsError;
  runsPanel.append(runsTitle, runs, runsError);

  content.append(form, runsPanel);
  section.append(header, content);
  return section;
}

function buildSkillForm() {
  const card = buildElement("div", "skill-form-card");

  const cardTitle = buildElement("div", "form-section-title");
  cardTitle.textContent = "新しいスキルを登録";
  card.appendChild(cardTitle);

  const form = buildElement("form", null, { id: "skill-form" });
  refs.skillForm = form;

  const nameGroup = buildElement("div", "form-group");
  const nameLabel = buildElement("label");
  nameLabel.textContent = "スキル名";
  const nameInput = buildElement("input", "form-input", { type: "text", placeholder: "例: Slack通知", required: "" });
  refs.nameInput = nameInput;
  nameGroup.append(nameLabel, nameInput);

  const descGroup = buildElement("div", "form-group");
  const descLabel = buildElement("label");
  descLabel.textContent = "説明（AIがいつ使うかを書く）";
  const descInput = buildElement("textarea", "form-textarea", { placeholder: "例: ユーザーへの通知が必要なときにSlackにメッセージを送る", required: "" });
  refs.descInput = descInput;
  descGroup.append(descLabel, descInput);

  const urlGroup = buildElement("div", "form-group");
  const urlLabel = buildElement("label");
  urlLabel.textContent = "Webhook URL";
  const urlInput = buildElement("input", "form-input", { type: "url", placeholder: "https://...", required: "" });
  refs.urlInput = urlInput;
  urlGroup.append(urlLabel, urlInput);

  const methodGroup = buildElement("div", "form-group");
  const methodLabel = buildElement("label");
  methodLabel.textContent = "HTTPメソッド";
  const methodSelect = buildElement("select", "form-select");
  const optPost = buildElement("option", null, { value: "POST" });
  optPost.textContent = "POST";
  const optGet = buildElement("option", null, { value: "GET" });
  optGet.textContent = "GET";
  methodSelect.append(optPost, optGet);
  refs.methodSelect = methodSelect;
  methodGroup.append(methodLabel, methodSelect);

  const bodyGroup = buildElement("div", "form-group");
  const bodyLabel = buildElement("label");
  bodyLabel.textContent = "ボディテンプレート（任意）";
  const bodyInput = buildElement("textarea", "form-textarea", { placeholder: '{"text": "{input}"}' });
  refs.bodyInput = bodyInput;
  const bodyHint = buildElement("p", "form-hint");
  bodyHint.textContent = '{input} がAIの入力テキストに置き換わります。空の場合は {"input": "..."} が自動送信されます。';
  bodyGroup.append(bodyLabel, bodyInput, bodyHint);

  const formError = buildElement("p", "form-error");
  refs.formError = formError;

  const submitBtn = buildElement("button", "btn-primary", { type: "submit" });
  submitBtn.textContent = "登録する";
  refs.submitBtn = submitBtn;

  form.append(nameGroup, descGroup, urlGroup, methodGroup, bodyGroup, formError, submitBtn);
  form.addEventListener("submit", handleFormSubmit);
  card.appendChild(form);
  return card;
}

function init() {
  const sidebar = buildSidebar(refs);

  const layout = buildElement("div", "skills-layout");
  const main = buildElement("div", "skills-main");

  const title = buildElement("h1", "page-title");
  title.textContent = "スキル管理";

  const formSection = buildSkillForm();
  const assistantSection = buildAssistantCard();
  const automationSection = buildAutomationSection();

  const listTitle = buildElement("div", "section-title");
  listTitle.textContent = "登録済みスキル";

  const skillList = buildElement("div", "skill-list");
  refs.skillList = skillList;

  main.append(title, automationSection, assistantSection, formSection, listTitle, skillList);
  layout.append(sidebar, main);
  document.body.appendChild(layout);

  loadSkills();
  loadAutomationRuns();
}

document.addEventListener("DOMContentLoaded", init);
