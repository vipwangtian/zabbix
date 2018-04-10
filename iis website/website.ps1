param ([string] $name = 0, [string] $type = 1)
if($type -eq "breceived")
{
    $ret = (Get-Counter -Counter "\Web Service($name)\Bytes Received/sec").CounterSamples[0].CookedValue
}
elseif($type -eq "bsent")
{
    $ret = (Get-Counter -Counter "\Web Service($name)\Bytes Sent/sec").CounterSamples[0].CookedValue
}
else
{
    $ret = (Get-Counter -Counter "\Web Service($name)\Current Connections").CounterSamples[0].CookedValue
}
write-host $ret