# 授权检测帮助模块
# @author Zhj<2024-08-10>


from functools import wraps
from public.exceptions import NoAuthorizationException


# 专业版用户限定装饰器
def only_pro_members(func: callable) -> callable:
    @wraps(func)
    def _wrap_func(*args, **kwargs):
        import PluginLoader

        if PluginLoader.get_auth_state() < 1:
            raise NoAuthorizationException('Sorry. This feature is professional member only.')

        return func(*args, **kwargs)

    return _wrap_func
