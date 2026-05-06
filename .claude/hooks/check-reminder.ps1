$reminders = @()

# 1. 未コミットのコード変更チェック
$uncommitted = git diff --name-only HEAD 2>$null |
    Where-Object { $_ -match '\.(py|js|html|css|json|ts)$' } |
    Where-Object { $_ -notmatch 'settings.*json$' }

if ($uncommitted) {
    $files = $uncommitted -join ', '
    $reminders += "[CHECK REMINDER] 未レビューのコード変更があります: $files"
    $reminders += "-> senior-code-reviewer で Check を実施してください。"
}

# 2. オープンPRのレビュー状態チェック
$prJson = gh pr view --json number,reviewDecision,state 2>$null
if ($prJson) {
    $pr = $prJson | ConvertFrom-Json
    if ($pr.state -eq 'OPEN' -and $pr.reviewDecision -ne 'APPROVED') {
        $reminders += "[PR REMINDER] PR #$($pr.number) が未レビューまたは未承認です。"
        $reminders += "-> /review スキルで PR最終レビューを実施してください。"
    }
}

foreach ($msg in $reminders) {
    Write-Output $msg
}
