#!/usr/bin/env pwsh
# Aggregate all SPR memory files into a single spr-index.md
# Optionally injects the index into AGENTS.md between sentinel comments.
[CmdletBinding()]
param(
    [switch]$InjectAgents,   # Also write the index into AGENTS.md
    [switch]$Help
)
$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Host "Usage: ./aggregate-spr.ps1 [-InjectAgents]"
    Write-Host ""
    Write-Host "Concatenates all .specify/memory/spr-*.md files into"
    Write-Host ".specify/memory/spr-index.md for use as AI context."
    Write-Host ""
    Write-Host "  -InjectAgents   Also injects the index into AGENTS.md"
    Write-Host "                  between <!-- SPR-MEMORY START/END --> sentinels."
    exit 0
}

function Find-RepositoryRoot {
    param([string]$StartDir, [string[]]$Markers = @('.git', '.specify'))
    $current = Resolve-Path $StartDir
    while ($true) {
        foreach ($marker in $Markers) {
            if (Test-Path (Join-Path $current $marker)) { return $current }
        }
        $parent = Split-Path $current -Parent
        if ($parent -eq $current) { return $null }
        $current = $parent
    }
}

$repoRoot = $null
try {
    $repoRoot = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0) { $repoRoot = $null }
} catch {}
if (-not $repoRoot) { $repoRoot = Find-RepositoryRoot -StartDir $PSScriptRoot }
if (-not $repoRoot) { Write-Error "Could not locate repository root."; exit 1 }

$memoryDir = Join-Path $repoRoot '.specify\memory'
$indexPath = Join-Path $memoryDir 'spr-index.md'

$sprFiles = Get-ChildItem -Path $memoryDir -Filter 'spr-*.md' -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -ne 'spr-index.md' } |
    Sort-Object Name

if ($sprFiles.Count -eq 0) {
    Write-Warning "No spr-*.md files found in $memoryDir"
    exit 0
}

$today = (Get-Date -Format 'yyyy-MM-dd')
$lines = @("# SPR Memory Index", "", "Auto-aggregated from $($sprFiles.Count) SPR file(s). Last updated: $today", "")

foreach ($file in $sprFiles) {
    $lines += "---"
    $lines += ""
    $lines += (Get-Content $file.FullName -Raw).TrimEnd()
    $lines += ""
}

Set-Content -Path $indexPath -Value ($lines -join "`n") -Encoding UTF8
Write-Output "Written : $indexPath ($($sprFiles.Count) files aggregated)"

if ($InjectAgents) {
    $agentsPath = Join-Path $repoRoot 'AGENTS.md'
    if (-not (Test-Path $agentsPath)) {
        Write-Warning "AGENTS.md not found at $agentsPath - skipping injection"
        exit 0
    }

    $startSentinel = '<!-- SPR-MEMORY START -->'
    $endSentinel   = '<!-- SPR-MEMORY END -->'
    $agentsContent = Get-Content $agentsPath -Raw

    $block = "$startSentinel`n`n## SPR Memory`n`n$(Get-Content $indexPath -Raw)`n$endSentinel"

    $escapedStart = [regex]::Escape($startSentinel)
    $escapedEnd   = [regex]::Escape($endSentinel)
    $pattern = '(?s)' + $escapedStart + '.*?' + $escapedEnd
    if ($agentsContent -match $escapedStart) {
        # Replace existing block
        $agentsContent = $agentsContent -replace $pattern, $block
    } else {
        # Append block
        $agentsContent = $agentsContent.TrimEnd() + "`n`n$block`n"
    }

    Set-Content -Path $agentsPath -Value $agentsContent -Encoding UTF8
    Write-Output "Injected : $agentsPath"
}
