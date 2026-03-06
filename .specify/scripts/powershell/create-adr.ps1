#!/usr/bin/env pwsh
# Create a new Architecture Decision Record (ADR)
[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Help,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Title
)
$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Host "Usage: ./create-adr.ps1 <title>"
    Write-Host ""
    Write-Host "Creates a new Architecture Decision Record in .specify/decisions/"
    Write-Host "Auto-numbers ADRs sequentially (ADR-001, ADR-002, ...)."
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Json    Output in JSON format"
    Write-Host "  -Help    Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  ./create-adr.ps1 'Sparse vs dense FSM scoring'"
    Write-Host "  ./create-adr.ps1 'Use slots for all core classes'"
    exit 0
}

if (-not $Title -or $Title.Count -eq 0) {
    Write-Error "Usage: ./create-adr.ps1 <title>"
    exit 1
}

$titleStr = ($Title -join ' ').Trim()

# Locate repository root
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

if (-not $repoRoot) {
    $repoRoot = Find-RepositoryRoot -StartDir $PSScriptRoot
}
if (-not $repoRoot) {
    Write-Error "Could not locate repository root."
    exit 1
}

Set-Location $repoRoot

$decisionsDir = Join-Path $repoRoot '.specify\decisions'
New-Item -ItemType Directory -Path $decisionsDir -Force | Out-Null

# Auto-number: find highest existing ADR-NNN
$highest = 0
Get-ChildItem -Path $decisionsDir -Filter 'ADR-*.md' -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.Name -match '^ADR-(\d+)') {
        $num = [int]$matches[1]
        if ($num -gt $highest) { $highest = $num }
    }
}
$nextNum = $highest + 1
$numStr = '{0:000}' -f $nextNum

# Build slug from title
$slug = $titleStr.ToLower() -replace '[^a-z0-9]', '-' -replace '-{2,}', '-' -replace '^-|-$', ''
$slug = ($slug -split '-' | Where-Object { $_.Length -ge 3 } | Select-Object -First 5) -join '-'
if (-not $slug) { $slug = 'decision' }

$fileName = "ADR-$numStr-$slug.md"
$adrPath  = Join-Path $decisionsDir $fileName

# Copy template and patch the header line
$template = Join-Path $repoRoot '.specify\templates\adr-template.md'
if (Test-Path $template) {
    $content = Get-Content $template -Raw
    $today = (Get-Date -Format 'yyyy-MM-dd')
    $content = $content -replace 'ADR-\[NNN\]: \[TITLE\]', "ADR-$numStr`: $titleStr"
    $content = $content -replace '\[YYYY-MM-DD\]', $today
    Set-Content -Path $adrPath -Value $content -Encoding UTF8
} else {
    New-Item -ItemType File -Path $adrPath | Out-Null
}

if ($Json) {
    [PSCustomObject]@{
        ADR_NUMBER = $numStr
        ADR_FILE   = $adrPath
        TITLE      = $titleStr
    } | ConvertTo-Json -Compress
} else {
    Write-Output "ADR_NUMBER : $numStr"
    Write-Output "ADR_FILE   : $adrPath"
    Write-Output "TITLE      : $titleStr"
}
