---
name: quick-form-filler
description: フォーム入力を高速化する軽量スキル
---

# Quick Form Filler

## 概要

DOM上のフォーム要素を自動入力する軽量スキルです。JavaScriptを使用し、複数フィールドへの一括入力に対応しています。Kyosistプロジェクトの共有フレームワーク（`public/common/`）として汎用化を想定しています。

## 責務

- **実施内容**: HTML フォーム（`<form>` / `<input>` / `<select>` / `<textarea>` 等）の要素を指定データで自動入力
- **範囲内**: テキスト入力、選択肢指定、チェックボックス / ラジオボタンの状態設定
- **範囲外**: ファイルアップロード、複雑なバリデーション、サーバー送信

## トリガー・いつ使うか

**使用場面**:
- テスト自動化でフォームを高速に埋めたい
- 同一フォーム構造の複数フォームに同じデータを入力したい
- UIレベルのテストで、フォーム入力ステップを短縮したい

**前提条件**:
- 対象フォーム要素が DOM に既に存在していること
- 入力フィールドに一意の識別子（`id` / `name` / `data-testid` 等）があること
- ブラウザ： Chrome 90+、Firefox 88+、Safari 14+

## 使用例

### 基本的な使い方

```javascript
// フォームデータを定義
const formData = {
  username: 'john_doe',
  email: 'john@example.com',
  country: 'JP',
  newsletter: true
};

// フォームを埋める
fillForm(formData, {
  formSelector: '#loginForm'
});
```

### セレクタ指定例

```javascript
// name 属性で照合
fillForm({
  'user[name]': 'Alice',
  'user[email]': 'alice@example.com'
}, {
  formSelector: 'form.user-profile'
});

// data-testid で照合（推奨）
fillForm({
  username: 'bob',
  password: 'securepass123'
}, {
  formSelector: '[data-testid="login-form"]'
});
```

## 手順（内部実装フロー）

1. **フォーム要素を特定** — `formSelector` から対象フォームをDOMから取得
2. **入力フィールドをマッピング** — データキーに対応するフィールドを探索（`id` / `name` / `data-*` で順序に検索）
3. **値を設定** — 各フィールドタイプ（text / checkbox / select等）に応じて適切に入力
4. **change イベントを発火** — UI の バリデーション / 動的フィールド表示をトリガー
5. **結果を返却** — 成功したフィールド数・失敗したフィールドを報告

## API 仕様

### 関数シグネチャ

```javascript
/**
 * フォーム要素を自動入力する
 * 
 * @param {Object} data - キー=フィールド識別子、値=入力値
 * @param {Object} options - 設定オプション
 * @param {string} options.formSelector - フォーム要素のセレクタ（必須）
 * @param {Array<string>} [options.fieldPriority=['id', 'name', 'data-testid']] 
 *   フィールド照合の優先順位（デフォルト: id > name > data-testid）
 * @param {boolean} [options.triggerChange=true] - change イベントを発火するか
 * @param {boolean} [options.validate=false] - 入力後にフォームバリデーションを実行するか
 * @returns {Object} 
 *   {
 *     success: boolean,          // 全フィールド入力成功か
 *     filled: number,            // 正常に入力されたフィールド数
 *     skipped: number,           // スキップされたフィールド数
 *     errors: Array<string>,     // エラーメッセージ配列
 *     failedFields: Object       // キー=フィールド名、値=失敗理由
 *   }
 */
function fillForm(data, options = {}) {
  // 実装詳細は下記参照
}
```

### 入力値の仕様

| フィールドタイプ | 入力例 | 説明 |
|---|---|---|
| `<input type="text">` | `{ username: 'alice' }` | テキストをそのまま設定 |
| `<input type="checkbox">` | `{ agree: true }` | true でチェック、false で未チェック |
| `<input type="radio">` | `{ gender: 'female' }` | ラジオボタンの value と照合 |
| `<select>` | `{ country: 'JP' }` | option の value と照合 |
| `<textarea>` | `{ message: 'Hello' }` | テキストをそのまま設定 |

### 返却値例

```javascript
{
  success: true,
  filled: 4,
  skipped: 0,
  errors: [],
  failedFields: {}
}
```

失敗例：

```javascript
{
  success: false,
  filled: 2,
  skipped: 1,
  errors: [
    'Field "email" not found in form'
  ],
  failedFields: {
    email: 'Field selector mismatch'
  }
}
```

## 実装サンプル

```javascript
/**
 * フォーム要素を自動入力する
 * 内部実装（vanilla JS、フレームワーク依存なし）
 */
function fillForm(data, options = {}) {
  const {
    formSelector,
    fieldPriority = ['id', 'name', 'data-testid'],
    triggerChange = true,
    validate = false
  } = options;

  // 入力値バリデーション
  if (!formSelector) {
    return {
      success: false,
      filled: 0,
      skipped: 0,
      errors: ['formSelector is required'],
      failedFields: {}
    };
  }

  const form = document.querySelector(formSelector);
  if (!form) {
    return {
      success: false,
      filled: 0,
      skipped: 0,
      errors: [`Form not found: ${formSelector}`],
      failedFields: {}
    };
  }

  let filled = 0;
  let skipped = 0;
  const errors = [];
  const failedFields = {};

  // 各データキーに対して入力を実施
  for (const [key, value] of Object.entries(data)) {
    let field = null;

    // 優先順位に従ってフィールドを探索
    for (const priority of fieldPriority) {
      if (priority === 'id') {
        field = form.querySelector(`#${key}`);
      } else if (priority === 'name') {
        field = form.querySelector(`[name="${key}"]`);
      } else if (priority === 'data-testid') {
        field = form.querySelector(`[data-testid="${key}"]`);
      }
      if (field) break;
    }

    if (!field) {
      skipped++;
      const msg = `Field "${key}" not found in form`;
      errors.push(msg);
      failedFields[key] = msg;
      continue;
    }

    try {
      // フィールドタイプに応じて入力
      if (field.type === 'checkbox') {
        field.checked = Boolean(value);
      } else if (field.type === 'radio') {
        const radio = form.querySelector(`[name="${field.name}"][value="${value}"]`);
        if (radio) {
          radio.checked = true;
        } else {
          throw new Error(`Radio option "${value}" not found`);
        }
      } else if (field.tagName === 'SELECT') {
        field.value = value;
        if (field.value !== String(value)) {
          throw new Error(`Option "${value}" not found in select`);
        }
      } else {
        // text, textarea, email, etc.
        field.value = value;
      }

      // change イベントを発火（バリデーション・UI更新をトリガー）
      if (triggerChange) {
        field.dispatchEvent(new Event('change', { bubbles: true }));
        field.dispatchEvent(new Event('input', { bubbles: true }));
      }

      filled++;
    } catch (err) {
      skipped++;
      const msg = `Failed to fill field "${key}": ${err.message}`;
      errors.push(msg);
      failedFields[key] = err.message;
    }
  }

  // オプション: フォーム全体をバリデーション
  if (validate && form.reportValidity) {
    form.reportValidity();
  }

  return {
    success: Object.keys(failedFields).length === 0,
    filled,
    skipped,
    errors,
    failedFields
  };
}
```

## 制限事項・対応範囲外

- **ファイルアップロード**: `<input type="file">` はセキュリティ上サポートしません
- **複合バリデーション**: 複雑なバリデーション（クロスフィールドチェック）は含めません
- **非同期処理**: 非同期バリデーション・API呼び出しはスコープ外です
- **shadow DOM**: Shadow DOM 内のフォーム要素はサポートしていません

## パフォーマンス

- 単一フォーム（10フィールド以下）: 1～5ms
- 大規模フォーム（100フィールド以上）: 20～50ms
- 環境依存: ブラウザエンジン・DOM複雑度に依存

## トラブルシューティング

### 症状：フィールドが埋まらない

**確認項目**:

1. フォームセレクタが正しいか確認
   ```javascript
   console.log(document.querySelector('#myForm')); // null でないか確認
   ```

2. フィールド識別子が一致しているか確認
   ```javascript
   // HTML側
   <input id="username" type="text">
   
   // データ側
   { username: 'john' }  // id が合致
   ```

3. ブラウザのコンソールでエラーが出ていないか確認
   ```javascript
   const result = fillForm(data, { formSelector: '#myForm' });
   console.log(result.errors); // エラー内容を確認
   ```

### 症状：change イベントが発火しない

**原因**: `triggerChange: false` に設定されているか、イベントリスナーがない

**対応**:
```javascript
fillForm(data, {
  formSelector: '#myForm',
  triggerChange: true  // デフォルト true
});
```

### 症状：select フィールドの値が設定されない

**確認項目**: option の value 属性と入力値が完全に一致しているか

```javascript
// HTML
<select name="country">
  <option value="JP">Japan</option>
  <option value="US">United States</option>
</select>

// 正しい入力
{ country: 'JP' }  // value 属性の値を使う

// 誤り
{ country: 'Japan' }  // label ではなく value を使う
```

## ブラウザ互換性

| ブラウザ | バージョン | 対応状況 |
|---|---|---|
| Chrome | 90+ | ✅ 完全対応 |
| Firefox | 88+ | ✅ 完全対応 |
| Safari | 14+ | ✅ 完全対応 |
| Edge | 90+ | ✅ 完全対応 |
| IE 11 | - | ❌ 非対応 |

## その他

- このスキルは Kyosist プロジェクトの `public/common/` に配置予定です
- 他プロジェクトでの再利用を想定し、フレームワーク依存を排除しています
- ラムダ式・無名関数は使用していません（コーディング規約準拠）
