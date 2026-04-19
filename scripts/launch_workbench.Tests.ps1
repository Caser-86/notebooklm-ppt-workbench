Set-StrictMode -Version Latest

. "$PSScriptRoot\launch_workbench.ps1"

Describe "Invoke-LaunchPreflight" {
    It "passes when commands, dependencies, and ports are ready" {
        Mock Test-LaunchCommand { $true }
        Mock Test-AgentImports {
            [pscustomobject]@{
                Status = "ok"
                Message = "Agent imports ok."
                Fix = ""
            }
        }
        Mock Test-WebDependencies {
            [pscustomobject]@{
                Status = "ok"
                Message = "web/node_modules exists."
                Fix = ""
            }
        }
        Mock Get-PortConflictInfo { $null }

        $result = Invoke-LaunchPreflight -WorkspaceRoot "D:\workspace"

        $result.Passed | Should Be $true
        @($result.Checks | Where-Object { $_.Status -ne "ok" }).Count | Should Be 0
    }

    It "fails when dependencies are missing or ports are busy" {
        Mock Test-LaunchCommand {
            param($CommandName)
            $CommandName -ne "python"
        }
        Mock Test-AgentImports {
            [pscustomobject]@{
                Status = "missing"
                Message = "Missing agent imports."
                Fix = "cd agent && python -m pip install -e .[dev]"
            }
        }
        Mock Test-WebDependencies {
            [pscustomobject]@{
                Status = "missing"
                Message = "web/node_modules is missing."
                Fix = "cd web && npm install"
            }
        }
        Mock Get-PortConflictInfo {
            param($Port)
            if ($Port -eq 8000) {
                [pscustomobject]@{
                    Port = 8000
                    ProcessId = 100
                    ProcessName = "python"
                }
            }
        }

        $result = Invoke-LaunchPreflight -WorkspaceRoot "D:\workspace"

        $result.Passed | Should Be $false
        ($result.Checks | Where-Object { $_.Name -eq "python" }).Status | Should Be "missing"
        ($result.Checks | Where-Object { $_.Name -eq "web_dependencies" }).Status | Should Be "missing"
        ($result.Checks | Where-Object { $_.Name -eq "port_8000" }).Status | Should Be "busy"
    }
}
