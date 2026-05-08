---
name: architecture
description: アーキテクチャ指針（段階的開示ディレクトリ設計、汎用フレームワーク作成）
---

# アーキテクチャ指針

## 段階的開示を意識したディレクトリ構成

ディレクトリ構造は「最もよく使うものが最も浅い階層にある」設計にする:

```
public/
├── index.html        # エントリポイント（最上位）
├── common/           # 全ページ共通のユーティリティ（次のレイヤー）
│   ├── framework.js  # 汎用フレームワーク（DOM生成等）
│   ├── base.css
│   └── sidebar.js
└── <feature>/        # 機能ごとのディレクトリ（最も深いレイヤー）
    ├── index.html
    ├── main.js
    └── style.css
```

ルール:
- 機能固有のコードは `public/<feature>/` に配置する
- 複数機能で共有されるコードは `public/common/` に移動する
- `common/` には Kyosist 固有のロジックを含めない（フレームワーク層として保つ）

## 汎用フレームワークの並行開発

**プロジェクト進行と同時に** `public/common/framework.js` へ汎用ユーティリティを抽出していく。
このフレームワークは **他のプロジェクトでも再利用する** ため、以下の設計原則を守る:

### 設計原則
- Kyosist 固有のロジック・定数・エンドポイントを含めない
- 関数は単一責任（1関数 = 1つのことだけ行う）
- 外部ライブラリへの依存ゼロ（Vanilla JS のみ）
- JSDoc コメントで入出力の型と使い方を明記する

### 抽出対象の例
- DOM生成メソッド（要素作成・属性付与・挿入）
- イベント委譲ヘルパー
- fetch ラッパー（共通エラーハンドリング付き）
- ローカルストレージ操作ユーティリティ
- フォームバリデーションユーティリティ

### 実装パターン
```javascript
// NG: Kyosist 固有のロジックが混入
function createChatMessage(text) { ... }

// OK: 汎用的なDOM生成関数として抽出
/**
 * 指定した要素を生成して属性・テキストを設定する
 * @param {string} tag - タグ名
 * @param {Object} attrs - 属性のキーと値
 * @param {string} [text] - テキストコンテンツ
 * @returns {HTMLElement}
 */
function createElement(tag, attrs = {}, text = '') { ... }
```
