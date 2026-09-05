$procs = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
    Where-Object { $_.CommandLine -match "bot\.main" }

if (-not $procs) {
    Write-Host "No running bot process found."
    exit 0
}

foreach ($p in $procs) {
    Stop-Process -Id $p.ProcessId -Force
    Write-Host "Stopped PID $($p.ProcessId)"
}
