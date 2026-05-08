# Assertion Grading Guide for agent-evaluator

## 採点基準

各テストケースのアサーション評価方法を定義します。

### テストケース 0: low-score-skill

#### Assertion 1: 複数のイテレーション（最小3回）が実行された

**PASS条件:**
- improvement_log.md に「Iteration 1」「Iteration 2」「Iteration 3」が明確に記載されている
- 各イテレーションで異なる改善が記述されている
- 最低3回のサイクルが完了している

**FAIL条件:**
- イテレーション数が3未満
- イテレーションの記載が曖昧
- 同じ改善が繰り返されている

**判定方法:**
improvement_log.md を読み、イテレーション数をカウント

---

#### Assertion 2: 最終スコアが95点以上に達成された

**PASS条件:**
- score_history.json の最終エントリで score >= 95
- または improvement_log.md に「最終スコア: 95点以上」と明記

**FAIL条件:**
- 最終スコア < 95
- スコアが不明

**判定方法:**
score_history.json の最後のスコア値を確認、または improvement_log.md から抽出

---

#### Assertion 3: 各イテレーションで SKILL.md が改善された

**PASS条件:**
- final_skill.md の内容が初期 SKILL.md より以下の点で改善されている:
  - 説明がより具体的・明確
  - セクションが追加または整理されている
  - 例やアンチパターンが追加されている
- improvement_log.md に各イテレーションの改善内容が記述されている

**FAIL条件:**
- final_skill.md が初期 SKILL.md と全く変わらない
- improvement_log.md に改善内容の記載がない

**判定方法:**
initial SKILL.md と final_skill.md を比較、improvement_log.md に改善内容が記載されているか確認

---

#### Assertion 4: 改善前後のスコア差が20点以上

**PASS条件:**
- score_history.json で「初期スコア」と「最終スコア」の差 >= 20点

**FAIL条件:**
- 改善幅 < 20点
- スコアが記載されていない

**判定方法:**
score_history.json から最初と最後のスコアを取得し、差分を計算

---

### テストケース 1: medium-score-skill

#### Assertion 1: 初期スコアから最低10点以上の改善が達成された

**PASS条件:**
- score_history.json で 改善幅 >= 10点

**FAIL条件:**
- 改善幅 < 10点

**判定方法:**
score_history.json から計算

---

#### Assertion 2: 最終スコアが95点以上に達成された

**PASS条件:**
- 最終スコア >= 95点

**判定方法:**
score_history.json から最後のスコアを確認

---

#### Assertion 3: 改善内容が段階的で理にかなっている

**PASS条件:**
- improvement_log.md に各イテレーションの改善がリストアップされている
- 改善内容が論理的に段階的（例：説明→セクション追加→テスト調整）
- 各改善がスコア向上に貢献している

**FAIL条件:**
- 改善内容が無意味または不要な変更ばかり
- 段階的でない（ランダムな変更）

**判定方法:**
improvement_log.md の記述内容を読んで判定

---

### テストケース 2: already-good-skill

#### Assertion 1: スキルが95点以上に達成されたか、または改善が限定的と判定された

**PASS条件:**
- 最終スコア >= 95点、または
- improvement_log.md に「改善が限定的で、既に十分な品質である」と記載されている

**FAIL条件:**
- スコアが不明
- 判定が記載されていない

**判定方法:**
score_history.json と improvement_log.md から判定

---

#### Assertion 2: 不要な変更が加えられていない

**PASS条件:**
- final_skill.md が初期 SKILL.md と同等か、わずかな改善のみ
- improvement_log.md に「変更なし」または「軽微な改善」と記載

**FAIL条件:**
- final_skill.md が初期から大幅に変更されている
- 改善なしで無駄な変更が加えられている

**判定方法:**
initial SKILL.md と final_skill.md を比較

---

#### Assertion 3: 最終スコアが初期スコアと比較して5点以上改善されている（または変わらない）

**PASS条件:**
- 改善幅 >= -5点（スコアが下がっていない）
- より正確には：改善幅 >= 0点が理想

**FAIL条件:**
- スコアが5点以上低下している（品質低下）

**判定方法:**
score_history.json から計算

---

## グレーディング戦略

各アサーションは **スクリプト**で自動グレード可能です：

```python
import json

def grade_assertion(assertion_name, eval_id, outputs_dir):
    """
    アサーションを自動グレード
    
    Args:
        assertion_name: アサーションの名前
        eval_id: テストケースID (0, 1, 2)
        outputs_dir: outputs フォルダのパス
    
    Returns:
        {passed: bool, evidence: str}
    """
    
    with open(f"{outputs_dir}/score_history.json") as f:
        scores = json.load(f)
    
    with open(f"{outputs_dir}/improvement_log.md") as f:
        log = f.read()
    
    # 各テストケースのアサーション評価
    if eval_id == 0:  # low-score-skill
        if assertion_name == "複数のイテレーション（最小3回）が実行された":
            iterations = log.count("Iteration")
            passed = iterations >= 3
            evidence = f"Found {iterations} iterations"
            return {passed, evidence}
        
        elif assertion_name == "最終スコアが95点以上に達成された":
            final_score = scores[-1]["score"]
            passed = final_score >= 95
            evidence = f"Final score: {final_score}"
            return {passed, evidence}
        
        # ... 他のアサーションも同様
```

