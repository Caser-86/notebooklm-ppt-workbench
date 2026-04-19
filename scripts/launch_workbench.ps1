Set-StrictMode -Version Latest

function Test-LaunchCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CommandName
    )

    return $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

function Test-AgentImports {
    param(
        [Parameter(Mandatory = $true)]
        [string]$AgentRoot
    )

    try {
        Push-Location $AgentRoot
        python -c "import app.main" | Out-Null
        return [pscustomobject]@{
            Status = "ok"
            Message = "Agent imports are available."
            Fix = ""
        }
    } catch {
        return [pscustomobject]@{
            Status = "missing"
            Message = "Agent dependencies are missing or broken."
            Fix = "cd agent && python -m pip install -e .[dev]"
        }
    } finally {
        Pop-Location
    }
}

function Test-WebDependencies {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WebRoot
    )

    $nodeModules = Join-Path $WebRoot "node_modules"
    if (Test-Path $nodeModules) {
        return [pscustomobject]@{
            Status = "ok"
            Message = "web/node_modules exists."
            Fix = ""
        }
    }

    return [pscustomobject]@{
        Status = "missing"
        Message = "web/node_modules is missing."
        Fix = "cd web && npm install"
    }
}

function Get-PortConflictInfo {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    try {
        if (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue) {
            $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($null -ne $connection) {
                $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
                return [pscustomobject]@{
                    Port = $Port
                    ProcessId = $connection.OwningProcess
                    ProcessName = if ($process) { $process.ProcessName } else { "unknown" }
                }
            }
        }
    } catch {
        return $null
    }

    return $null
}

function Invoke-LaunchPreflight {
    param(
        [string]$WorkspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
        [int]$AgentPort = 8000,
        [int]$WebPort = 5174
    )

    $agentRoot = Join-Path $WorkspaceRoot "agent"
    $webRoot = Join-Path $WorkspaceRoot "web"
    $checks = @()

    foreach ($commandName in @("python", "node", "npm")) {
        $available = Test-LaunchCommand -CommandName $commandName
        $checks += [pscustomobject]@{
            Name = $commandName
            Status = if ($available) { "ok" } else { "missing" }
            Message = if ($available) { "$commandName is available." } else { "$commandName is missing." }
            Fix = if ($available) { "" } else { "Install $commandName and add it to PATH." }
        }
    }

    $agentImportCheck = if (($checks | Where-Object Name -eq "python").Status -eq "ok") {
        Test-AgentImports -AgentRoot $agentRoot
    } else {
        [pscustomobject]@{
            Status = "missing"
            Message = "Agent dependency check skipped because python is missing."
            Fix = "Install python first."
        }
    }
    $checks += [pscustomobject]@{
        Name = "agent_dependencies"
        Status = $agentImportCheck.Status
        Message = $agentImportCheck.Message
        Fix = $agentImportCheck.Fix
    }

    $webCheck = Test-WebDependencies -WebRoot $webRoot
    $checks += [pscustomobject]@{
        Name = "web_dependencies"
        Status = $webCheck.Status
        Message = $webCheck.Message
        Fix = $webCheck.Fix
    }

    foreach ($port in @($AgentPort, $WebPort)) {
        $conflict = Get-PortConflictInfo -Port $port
        $checks += [pscustomobject]@{
            Name = "port_$port"
            Status = if ($null -eq $conflict) { "ok" } else { "busy" }
            Message = if ($null -eq $conflict) {
                "Port $port is available."
            } else {
                "Port $port is already in use by $($conflict.ProcessName) ($($conflict.ProcessId))."
            }
            Fix = if ($null -eq $conflict) { "" } else { "Stop the process using port $port before starting the workbench." }
        }
    }

    [pscustomobject]@{
        WorkspaceRoot = $WorkspaceRoot
        AgentRoot = $agentRoot
        WebRoot = $webRoot
        Checks = @($checks)
        Passed = @($checks | Where-Object { $_.Status -ne "ok" }).Count -eq 0
        AgentPort = $AgentPort
        WebPort = $WebPort
    }
}

function Write-LaunchPreflightReport {
    param(
        [Parameter(Mandatory = $true)]
        $Result
    )

    Write-Host "Workbench launch preflight"
    Write-Host "Workspace: $($Result.WorkspaceRoot)"
    foreach ($check in $Result.Checks) {
        Write-Host ""
        Write-Host "$($check.Name): $($check.Status)"
        Write-Host "$($check.Message)"
        if ($check.Fix) {
            Write-Host "Fix: $($check.Fix)"
        }
    }
}

function Start-WorkbenchProcesses {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorkspaceRoot,
        [int]$AgentPort = 8000,
        [int]$WebPort = 5174
    )

    $agentRoot = Join-Path $WorkspaceRoot "agent"
    $webRoot = Join-Path $WorkspaceRoot "web"

    $agent = Start-Process powershell.exe -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$agentRoot'; python -m uvicorn app.main:app --host 127.0.0.1 --port $AgentPort --reload"
    ) -PassThru

    $worker = Start-Process powershell.exe -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$agentRoot'; python -m app.worker"
    ) -PassThru

    $web = Start-Process powershell.exe -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$webRoot'; npm run dev -- --host 127.0.0.1 --port $WebPort"
    ) -PassThru

    [pscustomobject]@{
        Agent = $agent
        Worker = $worker
        Web = $web
    }
}

function Wait-WorkbenchReady {
    param(
        [int]$AgentPort = 8000,
        [int]$WebPort = 5174,
        [int]$TimeoutSeconds = 60
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $agentReady = $false
    $webReady = $false

    while ((Get-Date) -lt $deadline) {
        if (-not $agentReady) {
            try {
                $health = Invoke-RestMethod -Uri "http://127.0.0.1:$AgentPort/health" -TimeoutSec 3
                $agentReady = $health.status -eq "ok"
            } catch {
                $agentReady = $false
            }
        }

        if (-not $webReady) {
            try {
                $response = Invoke-WebRequest -Uri "http://127.0.0.1:$WebPort/" -TimeoutSec 3 -UseBasicParsing
                $webReady = $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
            } catch {
                $webReady = $false
            }
        }

        if ($agentReady -and $webReady) {
            return $true
        }

        Start-Sleep -Seconds 2
    }

    return $false
}

if ($MyInvocation.InvocationName -ne '.') {
    $result = Invoke-LaunchPreflight
    Write-LaunchPreflightReport -Result $result

    if (-not $result.Passed) {
        exit 1
    }

    Start-WorkbenchProcesses -WorkspaceRoot $result.WorkspaceRoot -AgentPort $result.AgentPort -WebPort $result.WebPort | Out-Null

    if (-not (Wait-WorkbenchReady -AgentPort $result.AgentPort -WebPort $result.WebPort)) {
        Write-Host ""
        Write-Host "Workbench did not become ready in time."
        exit 1
    }

    Start-Process "http://127.0.0.1:$($result.WebPort)/"
}
