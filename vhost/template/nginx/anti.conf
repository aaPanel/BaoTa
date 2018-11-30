#防盗链配置
location ~ .*\.(<EXT_NAME>)$
{
    expires      30d;
    access_log /dev/null;
    valid_referers none blocked <DOMAINS>;
    if ($invalid_referer){
        return <CODE>;
    }
}