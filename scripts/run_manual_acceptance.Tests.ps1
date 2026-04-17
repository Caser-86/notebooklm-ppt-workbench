Set-StrictMode -Version Latest

. "$PSScriptRoot\run_manual_acceptance.ps1"

Describe "Invoke-AcceptanceChecks" {
    It "passes when samples, health, and artifacts are available" {
        $root = Join-Path $TestDrive "workspace-pass"
        $samplesRoot = Join-Path $root "samples\notebooklm_exports"
        $artifactsRoot = Join-Path $root "agent\data\artifacts"

        foreach ($name in @("link-heavy", "table-heavy", "icon-card")) {
            $scenarioPath = Join-Path $samplesRoot $name
            New-Item -ItemType Directory -Path $scenarioPath -Force | Out-Null
            Set-Content -Path (Join-Path $scenarioPath "README.md") -Value "sample"
            Set-Content -Path (Join-Path $scenarioPath "prompt.txt") -Value "prompt"
            Set-Content -Path (Join-Path $scenarioPath "source-manifest.json") -Value "{}"
            Set-Content -Path (Join-Path $scenarioPath "slide-1.png") -Value "png"
        }

        New-Item -ItemType Directory -Path $artifactsRoot -Force | Out-Null
        Set-Content -Path (Join-Path $artifactsRoot "editable-rebuild.pptx") -Value "pptx"

        $result = Invoke-AcceptanceChecks -WorkspaceRoot $root -SkipHealthCheck

        $result.Passed | Should Be $true
        @($result.Samples).Count | Should Be 3
        @($result.Samples | Where-Object { $_.Status -ne "ok" }).Count | Should Be 0
        $result.Artifacts.PptxCount | Should Be 1
    }

    It "fails when sample exports are missing" {
        $root = Join-Path $TestDrive "workspace-fail"
        $samplesRoot = Join-Path $root "samples\notebooklm_exports"

        foreach ($name in @("link-heavy", "table-heavy", "icon-card")) {
            $scenarioPath = Join-Path $samplesRoot $name
            New-Item -ItemType Directory -Path $scenarioPath -Force | Out-Null
            Set-Content -Path (Join-Path $scenarioPath "README.md") -Value "sample"
            Set-Content -Path (Join-Path $scenarioPath "prompt.txt") -Value "prompt"
            Set-Content -Path (Join-Path $scenarioPath "source-manifest.json") -Value "{}"
        }

        $result = Invoke-AcceptanceChecks -WorkspaceRoot $root -SkipHealthCheck

        $result.Passed | Should Be $false
        @($result.Samples | Where-Object { $_.Status -eq "missing_assets" }).Count | Should Be 3
    }
}
