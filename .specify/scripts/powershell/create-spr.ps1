#!/usr/bin/env pwsh
# Create a new Sparse Priming Representation (SPR) memory file
[CmdletBinding()]
param(
    [switch]$Json,
    [string]$Category = "",
    [switch]$Help,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Topic
)
$ErrorActionPreference = 'Stop'

$validCategories = @('core-api', 'validation', 'visualization', 'testing', 'tooling', 'architecture')

if ($Help) {
    Write-Host "Usage: ./create-spr.ps1 [-Category <cat>] <topic>"
    Write-Host ""
    Write-Host "Creates a new SPR memory file in .specify/memory/."
    Write-Host "SPRs are living documents - edit in place as understanding evolves."
    Write-Host ""
    Write-Host "Categories: $($validCategories -join ', ')"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  ./create-spr.ps1 -Category validation 'Validation scoring'"
    Write-Host "  ./create-spr.ps1 -Category core-api 'StateMachine hot path'"
    exit 0
}

if (-not $Topic -or $Topic.Count -eq 0) {
    Write-Error "Usage: ./create-spr.ps1 [-Category <cat>] <topic>"
    exit 1
}

$topicStr = ($Topic -join ' ').Trim()

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
if (-not $repoRoot) { $repoRoot = Find-RepositoryRoot -StartDir $PSScriptRoot }
if (-not $repoRoot) { Write-Error "Could not locate repository root."; exit 1 }

Set-Location $repoRoot

$memoryDir = Join-Path $repoRoot '.specify\memory'
New-Item -ItemType Directory -Path $memoryDir -Force | Out-Null

# Build filename slug
$slug = $topicStr.ToLower() -replace '[^a-z0-9]', '-' -replace '-{2,}', '-' -replace '^-|-$', ''
$slug = ($slug -split '-' | Where-Object { $_.Length -ge 3 } | Select-Object -First 4) -join '-'
if (-not $slug) { $slug = 'memory' }

$fileName = "spr-$slug.md"
$sprPath  = Join-Path $memoryDir $fileName

if (Test-Path $sprPath) {
    Write-Warning "SPR file already exists: $sprPath"
    Write-Warning "Edit it directly to update the memory."
    if ($Json) {
        [PSCustomObject]@{ SPR_FILE = $sprPath; TOPIC = $topicStr; EXISTS = $true } | ConvertTo-Json -Compress
    } else {
        Write-Output "SPR_FILE  : $sprPath"
        Write-Output "TOPIC     : $topicStr"
        Write-Output "STATUS    : already exists - edit in place"
    }
    exit 0
}

# Copy template and patch header
$template = Join-Path $repoRoot '.specify\templates\spr-template.md'
$today = (Get-Date -Format 'yyyy-MM-dd')

if (Test-Path $template) {
    $content = Get-Content $template -Raw
    $content = $content -replace 'SPR: \[TOPIC\]', "SPR: $topicStr"
    $content = $content -replace '\[YYYY-MM-DD\]', $today
    if ($Category -and $validCategories -contains $Category) {
        $content = $content -replace '\[core-api \| validation \| visualization \| testing \| tooling \| architecture\]', $Category
    }
    Set-Content -Path $sprPath -Value $content -Encoding UTF8
} else {
    New-Item -ItemType File -Path $sprPath | Out-Null
}

if ($Json) {
    [PSCustomObject]@{ SPR_FILE = $sprPath; TOPIC = $topicStr; EXISTS = $false } | ConvertTo-Json -Compress
} else {
    Write-Output "SPR_FILE  : $sprPath"
    Write-Output "TOPIC     : $topicStr"
    Write-Output "STATUS    : created — fill in the statements"
}
