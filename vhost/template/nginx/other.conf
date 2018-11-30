#允许请求SSL验证目录
location ~ \.well-known
{
    allow all;
}

#图片缓存设置
location ~ .*\.(gif|jpg|jpeg|png|bmp|swf|ico)$
{
    expires      30d;
    error_log /dev/null;
    access_log /dev/null;
}

#js/css缓存设置
location ~ .*\.(js|css)?$
{
    expires      12h;
    error_log /dev/null;
    access_log /dev/null;
}