---
name: coding-standards
description: コーディング規約（技術スタック固定、責務分離、DB最適化、バリデーション、エラーハンドリング、ラムダ禁止）
globs: ["**/*.py", "**/*.js", "**/*.html", "**/*.css"]
---

# コーディング規約

## ラムダ式・無名関数の禁止

すべての言語でラムダ式・無名関数を使わない。必ず名前付き関数として定義する。

```python
# NG
fn = lambda x: x * 2

# OK
def double(x):
    return x * 2
```

```javascript
// NG
const double = x => x * 2;
const arr = [1,2,3].map(x => x * 2);

// OK
function double(x) { return x * 2; }
const arr = [1,2,3].map(double);
```

## 技術スタックとバージョン固定

- **Python**: 3.11+ — 型ヒント必須、f-string 使用
- **JavaScript**: ES2020+ — `const`/`let` のみ（`var` 禁止）、モジュール構文（`import`/`export`）を使用
- **FastAPI**: 最新安定版 — Pydantic v2 モデルを使用
- Linter: Python=Ruff、JS=Oxlint

## 責務の明確な分離

SQLのデータ操作・ビジネスロジック・UI層を密結合させない:
- **データ層**: DB操作のみ（ビジネスロジックを含めない）
- **サービス層**: ビジネスロジックのみ（HTTP/UI依存を持たない）
- **API/UI層**: リクエスト受付とレスポンス生成のみ

## データベース操作の最適化

- N+1問題を回避する（ループ内でのクエリ発行禁止）
- インデックスを意識したクエリを書く
- SQLインジェクション防止のためプレースホルダー（バインド変数）を必ず使用

## 入力バリデーション

- ユーザ入力はすべてサニタイズ・バリデーションを行う
- FastAPI では Pydantic モデルで型・制約を定義する
- フロントエンドでの検証に加え、必ずバックエンドでも二重検証する

## エラーハンドリングの統一

- 例外を `except: pass` で握りつぶさない
- FastAPI: エラーは `HTTPException` で返す（辞書の直接返却禁止）
- フロントエンドへは人間が読めるエラーメッセージを返す
- スタックトレースを本番レスポンスに含めない
