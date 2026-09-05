$procs = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
    Where-Object { $_.CommandLine -match "bot\.main" }

if (-not $procs) {
    Write-Host "실행 중인 봇 프로세스가 없습니다."
    exit 0
}

foreach ($p in $procs) {
    Stop-Process -Id $p.ProcessId -Force
    Write-Host "종료: PID $($p.ProcessId)"
}
