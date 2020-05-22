# This function converts from one encoding to another.
function convertto-encoding ([string]$from, [string]$to){
    begin{
        $encfrom = [system.text.encoding]::getencoding($from)
        $encto = [system.text.encoding]::getencoding($to)
    }
    process{
        $bytes = $encto.getbytes($_)
        $bytes = [system.text.encoding]::convert($encfrom, $encto, $bytes)
        $encto.getstring($bytes)
    }
}

# First, grab our hostname
$SQLServer = $(hostname.exe)
$instances=@()
# Now, we find all services that start with MSSQL$ or MSSQLSERVER, and loop through them
Get-Service | Where-Object {($_.Name -like 'MSSQL$*' -or $_.Name -like 'MSSQLSERVER') -and $_.Status -eq 'Running'}| ForEach-Object{
    if ($_.Name -eq "MSSQLSERVER")
    {
        $instances += "SQLSERVER"
    }
    else
    {
        $instances += $_.NAME
    }
}

$idx = 1
write-host "{"
write-host " `"data`":[`n"
foreach ($inst in $instances)
{
    if ($idx -lt $instances.Count)
    {
        $line= "{ `"{#INST}`" : `"" + $inst + "`"}," | convertto-encoding "cp866" "utf-8"
        write-host $line
    }
    # If this is the last row, we print a slightly different string - one without the trailing comma
    # Although I don't think the trailing comma would technically break JSON, this is the right way
    # to do it.
    elseif ($idx -ge $instances.Count)
    {
        $line= "{ `"{#INST}`" : `"" + $inst + "`"}" | convertto-encoding "cp866" "utf-8"
        write-host $line
    }
    $idx++;
}
write-host
write-host " ]"
write-host "}"