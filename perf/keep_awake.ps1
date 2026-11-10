param([int]$Seconds = 2000)

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class SleepUtil {
    [DllImport("kernel32.dll")]
    public static extern uint SetThreadExecutionState(uint esFlags);
}
"@

$ES_CONTINUOUS = 0x80000000
$ES_SYSTEM_REQUIRED = 0x00000001
$ES_DISPLAY_REQUIRED = 0x00000002

[SleepUtil]::SetThreadExecutionState($ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED -bor $ES_DISPLAY_REQUIRED) | Out-Null
"keep-awake on for $Seconds seconds"
Start-Sleep -Seconds $Seconds
[SleepUtil]::SetThreadExecutionState($ES_CONTINUOUS) | Out-Null
"keep-awake off"
