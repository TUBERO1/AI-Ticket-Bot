$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$vbs = Join-Path $root "scripts\start_hidden.vbs"
$taskName = "AITicketBot"

if (-not (Test-Path $vbs)) {
    Write-Error "start_hidden.vbs를 찾을 수 없습니다: $vbs"
}

$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$vbs`""
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "AI Ticket Discord bot" -Force | Out-Null

Write-Host "등록 완료: $taskName"
Write-Host "로그인 시 백그라운드로 봇이 실행됩니다."
Write-Host "로그: $root\logs\bot.log"
Write-Host ""
Write-Host "지금 바로 실행하려면: wscript.exe `"$vbs`""
