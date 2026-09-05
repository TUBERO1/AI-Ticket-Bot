$taskName = "AITicketBot"

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "자동 실행 해제: $taskName"
