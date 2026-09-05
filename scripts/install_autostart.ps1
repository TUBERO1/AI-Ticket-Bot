$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$vbs = Join-Path $root "scripts\start_hidden.vbs"
$taskName = "AITicketBot"

if (-not (Test-Path $vbs)) {
    Write-Error "start_hidden.vbs not found: $vbs"
}

$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$vbs`""
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "AI Ticket Bot autostart" -Force | Out-Null

Write-Host "Registered: $taskName"
Write-Host "The bot will start in the background on login."
Write-Host "Log: $root\logs\bot.log"
Write-Host ""
Write-Host "Run now: wscript.exe `"$vbs`""
