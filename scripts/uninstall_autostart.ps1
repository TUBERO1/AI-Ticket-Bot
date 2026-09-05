$taskName = "AITicketBot"

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "Autostart removed: $taskName"
