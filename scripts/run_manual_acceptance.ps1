Set-StrictMode -Version Latest

function Test-AcceptanceSample {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ScenarioName,
        [Parameter(Mandatory = $true)]
        [string]$ScenarioPath
    )

    $requiredFiles = @("README.md", "prompt.txt", "source-manifest.json")
    $missingFiles = @($requiredFiles | Where-Object { -not (Test-Path (Join-Path $ScenarioPath $_)) })
    $slideExports = @(Get-ChildItem -Path $ScenarioPath -Filter "slide-*.png" -File -ErrorAction SilentlyContinue)
    $ocrJson = @(Get-ChildItem -Path $ScenarioPath -Filter "ocr.json" -File -ErrorAction SilentlyContinue)

    $status = if ($missingFiles.Count -gt 0) {
        "missing_files"
    } elseif ($slideExports.Count -eq 0) {
        "missing_assets"
    } else {
        "ok"
    }

    [pscustomobject]@{
        Name = $ScenarioName
        Path = $ScenarioPath
        Status = $status
        MissingFiles = $missingFiles
        SlideCount = $slideExports.Count
        HasOcrJson = $ocrJson.Count -gt 0
    }
}

function Test-AgentHealth {
    param(
        [Parameter(Mandatory = $true)]
        [string]$HealthUrl
    )

    try {
        $response = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 5
        if ($response.status -eq "ok") {
            return [pscustomobject]@{
                Status = "ok"
                Message = "Agent health endpoint responded with status ok."
            }
        }

        return [pscustomobject]@{
            Status = "unexpected"
            Message = "Agent health endpoint responded, but status was not ok."
        }
    } catch {
        return [pscustomobject]@{
            Status = "unreachable"
            Message = $_.Exception.Message
        }
    }
}

function Get-AcceptanceArtifacts {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ArtifactsRoot
    )

    $pptxFiles = @()
    if (Test-Path $ArtifactsRoot) {
        $pptxFiles = @(Get-ChildItem -Path $ArtifactsRoot -Recurse -Filter "*.pptx" -File -ErrorAction SilentlyContinue)
    }

    [pscustomobject]@{
        Root = $ArtifactsRoot
        PptxCount = $pptxFiles.Count
        Status = if ($pptxFiles.Count -gt 0) { "ok" } else { "missing_outputs" }
    }
}

function Invoke-AcceptanceChecks {
    param(
        [string]$WorkspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
        [string]$HealthUrl = "http://127.0.0.1:8000/health",
        [switch]$SkipHealthCheck
    )

    $samplesRoot = Join-Path $WorkspaceRoot "samples\notebooklm_exports"
    $artifactsRoot = Join-Path $WorkspaceRoot "agent\data\artifacts"
    $sampleNames = @("link-heavy", "table-heavy", "icon-card")
    $samples = @()

    foreach ($sampleName in $sampleNames) {
        $scenarioPath = Join-Path $samplesRoot $sampleName
        $samples += Test-AcceptanceSample -ScenarioName $sampleName -ScenarioPath $scenarioPath
    }

    $health = if ($SkipHealthCheck) {
        [pscustomobject]@{
            Status = "skipped"
            Message = "Health check skipped."
        }
    } else {
        Test-AgentHealth -HealthUrl $HealthUrl
    }

    $artifacts = Get-AcceptanceArtifacts -ArtifactsRoot $artifactsRoot

    $failingSamples = @($samples | Where-Object { $_.Status -ne "ok" })
    $passed = (
        ($health.Status -in @("ok", "skipped")) -and
        ($artifacts.Status -eq "ok") -and
        ($failingSamples.Count -eq 0)
    )

    [pscustomobject]@{
        WorkspaceRoot = $WorkspaceRoot
        Health = $health
        Artifacts = $artifacts
        Samples = @($samples)
        Passed = $passed
    }
}

function Write-AcceptanceReport {
    param(
        [Parameter(Mandatory = $true)]
        $Result
    )

    Write-Host "Acceptance summary"
    Write-Host "Workspace: $($Result.WorkspaceRoot)"
    Write-Host "Health: $($Result.Health.Status) - $($Result.Health.Message)"
    Write-Host "Artifacts: $($Result.Artifacts.Status) - $($Result.Artifacts.PptxCount) .pptx files found"

    foreach ($sample in $Result.Samples) {
        Write-Host ""
        Write-Host "Sample: $($sample.Name)"
        Write-Host "Status: $($sample.Status)"
        Write-Host "Slides: $($sample.SlideCount)"
        Write-Host "OCR JSON: $($sample.HasOcrJson)"
        if ($sample.MissingFiles.Count -gt 0) {
            Write-Host "Missing files: $($sample.MissingFiles -join ', ')"
        }
    }

    $overall = if ($Result.Passed) { "PASS" } else { "FAIL" }
    Write-Host ""
    Write-Host "Overall: $overall"
}

if ($MyInvocation.InvocationName -ne '.') {
    $result = Invoke-AcceptanceChecks
    Write-AcceptanceReport -Result $result
    if (-not $result.Passed) {
        exit 1
    }
}
