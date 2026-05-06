$thresholdPercent = 5.0
$cooldownMinutes = 30
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $utf8NoBom
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom
$rawInput = [Console]::In.ReadToEnd()

function Convert-ToPercent {
    param([object]$Value)

    if ($null -eq $Value) {
        return $null
    }

    $text = ([string]$Value).Trim()
    if (-not $text) {
        return $null
    }

    $text = $text.TrimEnd("%")
    $number = 0.0
    if (-not [double]::TryParse(
        $text,
        [System.Globalization.NumberStyles]::Float,
        [System.Globalization.CultureInfo]::InvariantCulture,
        [ref]$number
    )) {
        return $null
    }

    if ($number -ge 0 -and $number -le 1) {
        return $number * 100
    }

    return $number
}

function Find-CreditPercent {
    param([object]$Node)

    if ($null -eq $Node) {
        return $null
    }

    if ($Node -is [System.Array]) {
        foreach ($item in $Node) {
            $found = Find-CreditPercent $item
            if ($null -ne $found) {
                return $found
            }
        }
        return $null
    }

    if ($Node -is [System.Management.Automation.PSCustomObject]) {
        foreach ($property in $Node.PSObject.Properties) {
            $name = $property.Name
            $value = $property.Value

            if ($name -match '(?i)(credit|quota|limit|usage|token).*?(remaining|left|percent|pct)' -or
                $name -match '(?i)(remaining|left).*?(credit|quota|limit|usage|token)') {
                $percent = Convert-ToPercent $value
                if ($null -ne $percent) {
                    return $percent
                }
            }

            $nested = Find-CreditPercent $value
            if ($null -ne $nested) {
                return $nested
            }
        }
    }

    return $null
}

$creditPercent = $null

if ($rawInput) {
    try {
        $payload = $rawInput | ConvertFrom-Json
        $creditPercent = Find-CreditPercent $payload
    } catch {
        # Ignore malformed hook payloads; environment fallback below may still apply.
    }
}

if ($null -eq $creditPercent) {
    foreach ($name in @(
        "CLAUDE_CREDIT_REMAINING_PERCENT",
        "CLAUDE_REMAINING_CREDIT_PERCENT",
        "CREDIT_REMAINING_PERCENT",
        "REMAINING_CREDIT_PERCENT",
        "USAGE_REMAINING_PERCENT"
    )) {
        $percent = Convert-ToPercent ([Environment]::GetEnvironmentVariable($name))
        if ($null -ne $percent) {
            $creditPercent = $percent
            break
        }
    }
}

if ($null -eq $creditPercent -or $creditPercent -ge $thresholdPercent) {
    return
}

$handoffDir = ".claude/doc/session-handoffs"
$markerPath = Join-Path $handoffDir ".last-credit-handoff.json"
New-Item -ItemType Directory -Force -Path $handoffDir | Out-Null

if (Test-Path $markerPath) {
    try {
        $marker = Get-Content $markerPath -Raw | ConvertFrom-Json
        $lastGeneratedAt = [datetime]$marker.generated_at
        if (((Get-Date) - $lastGeneratedAt).TotalMinutes -lt $cooldownMinutes) {
            Write-Output "[CREDIT HANDOFF] Credit below threshold, but handoff was generated recently: $($marker.path)"
            return
        }
    } catch {
        # Ignore invalid marker and generate a fresh handoff.
    }
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$handoffPath = Join-Path $handoffDir "session-handoff-$timestamp.md"
$latestPath = Join-Path $handoffDir "latest-session-handoff.md"

$branch = git branch --show-current 2>$null
$head = git -c i18n.logOutputEncoding=utf-8 log -1 --oneline 2>$null
$status = git status --short 2>$null
$recentLog = git -c i18n.logOutputEncoding=utf-8 log --oneline -8 2>$null
$pendingTasks = ""
if (Test-Path ".claude/doc/pending-tasks.md") {
    $pendingTasks = Get-Content ".claude/doc/pending-tasks.md" -Raw
    if ($pendingTasks.Length -gt 12000) {
        $pendingTasks = $pendingTasks.Substring(0, 12000) + "`n`n[truncated]"
    }
}

$content = @"
# Session Handoff

Generated at: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz")
Reason: credit remaining below $thresholdPercent% (detected: $([Math]::Round($creditPercent, 2))%)

## Current Git Context

Branch: $branch

HEAD:
``````
$head
``````

Status:
``````
$($status -join "`n")
``````

Recent commits:
``````
$($recentLog -join "`n")
``````

## Pending Tasks Snapshot

``````markdown
$pendingTasks
``````

## Next Session Checklist

- Read `.claude/doc/pending-tasks.md`.
- Review this handoff file and current `git status`.
- Continue from unchecked `[ ]` items and preserve unrelated local changes.
- Update `.claude/doc/pending-tasks.md` before final completion.
"@

$content | Out-File -FilePath $handoffPath -Encoding UTF8
$content | Out-File -FilePath $latestPath -Encoding UTF8

$marker = @{
    generated_at = (Get-Date).ToString("o")
    credit_percent = $creditPercent
    path = $handoffPath
}
$marker | ConvertTo-Json | Out-File -FilePath $markerPath -Encoding UTF8

Write-Output "[CREDIT HANDOFF] Created $handoffPath"
