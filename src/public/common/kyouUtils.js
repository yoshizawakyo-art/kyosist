/**
 * 指定したタグ・CSSクラス・DOMプロパティを持つHTML要素を生成して返す。
 *
 * @param {string} tag - 生成する要素のHTMLタグ名（例: 'div', 'button', 'textarea'）
 * @param {string|null} className - 付与するCSSクラス名。null を渡すとクラスを設定しない
 * @param {object} [domProps={}] - DOMオブジェクトのプロパティとして直接代入するキー・値のペア
 *   （例: { id: 'main-content', rows: 3, placeholder: '入力してください' }）
 * @returns {HTMLElement} 生成されたDOM要素
 */
export function buildElement(tag, className, domProps = {}) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  Object.assign(element, domProps);
  return element;
}

/**
 * SVG名前空間でSVG要素を生成し、指定した属性を設定して返す。（内部ヘルパー）
 *
 * @param {string} tag - SVGタグ名（例: 'svg', 'path', 'line', 'circle'）
 * @param {object} [attrs={}] - setAttribute で設定する属性名と値のペア
 * @returns {SVGElement} 属性が設定されたSVG要素
 */
function buildSvgElement(tag, attrs = {}) {
  const svgElement = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [attrName, attrValue] of Object.entries(attrs)) {
    svgElement.setAttribute(attrName, attrValue);
  }
  return svgElement;
}

/**
 * サイドバーボタン用のストローク（線描き）スタイルSVGアイコンを生成して返す。
 * ボタン要素に appendChild することで視覚的なアイコンとして機能する。
 *
 * @param {string} innerSvgMarkup - SVGタグ内に挿入するパス・図形のHTMLマークアップ
 *   （例: '<line x1="12" y1="5" x2="12" y2="19"/>'）
 * @returns {SVGElement} CSSクラス "sb-icon" が付いたSVG要素
 */
export function buildSidebarIcon(innerSvgMarkup) {
  const svgElement = buildSvgElement("svg", {
    class: "sb-icon",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    "stroke-width": "2",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
  });
  svgElement.innerHTML = innerSvgMarkup;
  return svgElement;
}

/**
 * 送信ボタン内に表示する紙飛行機アイコン（SVG）を生成して返す。（内部ヘルパー）
 *
 * @returns {SVGElement} 15×15px の紙飛行機アイコン
 */
function buildSendIcon() {
  const svgElement = buildSvgElement("svg", {
    width: "15", height: "15",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    "stroke-width": "2.5",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
  });
  svgElement.innerHTML = `<line x1="22" y1="2" x2="11" y2="13"/>
                          <polygon points="22 2 15 22 11 13 2 9 22 2"/>`;
  return svgElement;
}

/**
 * 紙飛行機アイコンを内包した丸型の送信ボタンを生成して返す。
 *
 * @param {string} buttonId - ボタン要素に付与する id 属性値
 * @returns {HTMLButtonElement} CSSクラス "send-btn" が付いた送信ボタン
 */
export function buildSendButton(buttonId) {
  const button = buildElement("button", "send-btn", { id: buttonId, title: "送信" });
  button.appendChild(buildSendIcon());
  return button;
}

/**
 * テキストエリアと送信ボタンをまとめたカード型入力ボックスを生成して返す。
 * ウェルカム画面とチャット画面の両方で使用する共通入力UI。
 *
 * @param {string} textareaId - テキストエリアに付与する id 属性値
 * @param {string} buttonId - 送信ボタンに付与する id 属性値
 * @param {string} placeholder - テキストエリアに表示するプレースホルダーテキスト
 * @param {string} [boxClass="input-box"] - 外枠 div に付与するCSSクラス名
 * @returns {{ box: HTMLElement, textarea: HTMLTextAreaElement, button: HTMLButtonElement }}
 *   box: 外枠コンテナ / textarea: テキスト入力欄 / button: 送信ボタン
 */
export function buildInputBox(textareaId, buttonId, placeholder, boxClass = "input-box") {
  const container = buildElement("div", boxClass);
  const textarea  = buildElement("textarea", null, { id: textareaId, rows: 1, placeholder });
  const footer    = buildElement("div", "box-footer");
  const button    = buildSendButton(buttonId);
  footer.appendChild(button);
  container.append(textarea, footer);
  return { box: container, textarea, button };
}
