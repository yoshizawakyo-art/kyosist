/**
 * Create a DOM element with optional className and property assignments.
 * @param {string} tag
 * @param {string|null} className
 * @param {object} props  - assigned directly as DOM properties (id, rows, placeholder, …)
 */
export function el(tag, className, props = {}) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  Object.assign(node, props);
  return node;
}

/**
 * Create an SVG element in the SVG namespace.
 * @param {string} tag
 * @param {object} attrs - set via setAttribute
 */
function svgEl(tag, attrs = {}) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
}

/** Sidebar-sized icon (stroke-based SVG). */
export function icon(innerPaths) {
  const s = svgEl("svg", {
    class: "sb-icon",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    "stroke-width": "2",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
  });
  s.innerHTML = innerPaths;
  return s;
}

/** Paper-plane send icon for send buttons. */
function sendSvg() {
  const s = svgEl("svg", {
    width: "15", height: "15",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    "stroke-width": "2.5",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
  });
  s.innerHTML = `<line x1="22" y1="2" x2="11" y2="13"/>
                 <polygon points="22 2 15 22 11 13 2 9 22 2"/>`;
  return s;
}

/** Circular send button with paper-plane icon. */
export function buildSendBtn(id) {
  const btn = el("button", "send-btn", { id, title: "送信" });
  btn.appendChild(sendSvg());
  return btn;
}

/**
 * Card-style input box containing a textarea and a send button.
 * @param {string} taId       - id for the textarea
 * @param {string} btnId      - id for the send button
 * @param {string} placeholder
 * @param {string} boxClass   - CSS class for the wrapper div
 * @returns {{ box, ta, btn }}
 */
export function buildInputBox(taId, btnId, placeholder, boxClass = "input-box") {
  const box    = el("div", boxClass);
  const ta     = el("textarea", null, { id: taId, rows: 1, placeholder });
  const footer = el("div", "box-footer");
  const btn    = buildSendBtn(btnId);
  footer.appendChild(btn);
  box.append(ta, footer);
  return { box, ta, btn };
}
