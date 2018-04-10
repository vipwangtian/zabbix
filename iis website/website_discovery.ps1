Import-Module WebAdministration
$apppool = Get-ChildItem -Path IIS:\Sites | Where-Object {$_.State -eq "Started"} | Select-Object Name
$idx = 1
write-host "{"
write-host " `"data`":[`n"
foreach ($currentapppool in $apppool)
{
    if ($idx -lt $apppool.count)
    {
     
        $line= "{ `"{#APPPOOL}`" : `"" + $currentapppool.name + "`" },"
        write-host $line
    }
    elseif ($idx -ge $apppool.count)
    {
    $line= "{ `"{#APPPOOL}`" : `"" + $currentapppool.name + "`" }"
    write-host $line
    }
    $idx++;
}
write-host
write-host " ]"
write-host "}"