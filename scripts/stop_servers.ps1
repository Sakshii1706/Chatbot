# Stop Rasa (5005) and Action (5055) servers by port
# Usage: ./scripts/stop_servers.ps1

function Stop-ByPort {
    param([int]$Port)
    try {
        $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if ($null -eq $conns) {
            Write-Host "No process bound to port $Port"
            return
        }
        $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($pid in $pids) {
            try {
                $p = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($p) {
                    Write-Host "Stopping PID $pid ($($p.ProcessName)) on port $Port..."
                    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                } else {
                    Write-Host "Process $pid not found (already stopped?)"
                }
            } catch {
                Write-Host "Failed to stop PID $pid: $($_.Exception.Message)"
            }
        }
    } catch {
        Write-Host "Error inspecting port $Port: $($_.Exception.Message)"
    }
}

Stop-ByPort -Port 5005
Stop-ByPort -Port 5055

Write-Host "Done. You can restart with ./scripts/start_servers.ps1"