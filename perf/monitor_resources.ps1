param(
    [int]$AppPid,
    [int]$MysqlPid,
    [int]$Seconds = 1600,
    [string]$Out = "results/resources-step5min.csv"
)

$cores = [Environment]::ProcessorCount
"timestamp,app_cpu_pct,app_mem_mb,mysql_cpu_pct,mysql_mem_mb,disk_pct" | Set-Content -Encoding UTF8 $Out

for ($i = 0; $i -lt ($Seconds / 2); $i++) {
    Start-Sleep -Seconds 2
    try {
        $appRow = Get-CimInstance Win32_PerfFormattedData_PerfProc_Process -Filter "IDProcess=$AppPid" -ErrorAction Stop | Select-Object -First 1
        $dbRow = Get-CimInstance Win32_PerfFormattedData_PerfProc_Process -Filter "IDProcess=$MysqlPid" -ErrorAction Stop | Select-Object -First 1
        $diskRow = Get-CimInstance Win32_PerfFormattedData_PerfDisk_LogicalDisk -Filter "Name='_Total'" -ErrorAction Stop | Select-Object -First 1
    } catch {
        continue
    }
    if (-not $appRow -or -not $dbRow) { continue }

    $appCpu = [double]$appRow.PercentProcessorTime / $cores
    $dbCpu = [double]$dbRow.PercentProcessorTime / $cores
    $appMem = [math]::Round([double]$appRow.WorkingSet / 1MB, 1)
    $dbMem = [math]::Round([double]$dbRow.WorkingSet / 1MB, 1)
    $disk = if ($diskRow) { [math]::Round([double]$diskRow.PercentDiskTime, 1) } else { 0 }
    $now = Get-Date
    $line = "{0},{1},{2},{3},{4},{5}" -f $now.ToString("yyyy-MM-dd HH:mm:ss"),
        [math]::Round($appCpu, 1), $appMem, [math]::Round($dbCpu, 1), $dbMem, $disk
    Add-Content -Encoding UTF8 $Out $line
}
"done"
