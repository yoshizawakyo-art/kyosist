$rawInput = [Console]::In.ReadToEnd()
$changedPaths = @()

if ($rawInput) {
    try {
        $payload = $rawInput | ConvertFrom-Json
        $toolInput = $payload.tool_input

        foreach ($field in @("file_path", "path")) {
            if ($toolInput -and $toolInput.$field) {
                $changedPaths += [string]$toolInput.$field
            }
        }
    } catch {
        # Ignore malformed hook payloads; git diff fallback below still applies.
    }
}

$gitChanged = git diff --name-only HEAD 2>$null
if ($gitChanged) {
    $changedPaths += $gitChanged
}

$patterns = @(
    '^AGENTS\.md$',
    '^CLAUDE\.md$',
    '^\.claude/rules/',
    '^\.claude/skills/',
    '^\.codex/skills/',
    '^skills/',
    '\.codex[/\\]skills[/\\]'
)

$matched = $changedPaths |
    Where-Object { $_ } |
    Select-Object -Unique |
    Where-Object {
        $path = ($_ -replace '\\', '/')
        foreach ($pattern in $patterns) {
            if ($path -match $pattern) {
                return $true
            }
        }
        return $false
    }

if ($matched) {
    Write-Output "[RULE/SKILL SYNC REMINDER] Rule or skill changes detected."
    Write-Output "-> Check Codex-facing files and .claude counterparts, then sync them in the same turn when needed."
    Write-Output "-> Record synced / intentionally not synced / pending items in .claude/doc/pending-tasks.md."
}
