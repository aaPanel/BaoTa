from .exceptions import NoAuthorizationException, HintException


def get_module(filename: str):
    import PluginLoader

    module_obj = PluginLoader.get_module(filename)

    if not module_obj:
        raise ImportError(filename)

    if isinstance(module_obj, dict):
        if 'msg' not in module_obj:
            raise ImportError(filename)

        if module_obj['msg'] == 'Sorry. This feature is professional member only.':
            raise NoAuthorizationException(module_obj['msg'])

        if str(module_obj['msg']).find('Traceback ') > -1:
            raise RuntimeError('\n\n{}'.format(module_obj['msg']))

        raise ImportError('{}\n\n{}'.format(filename, module_obj['msg']))

    return module_obj
