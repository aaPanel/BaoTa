# Hook __import__
import builtins
import os
import sys
import public
import public.PluginLoader as plugin_loader


if 'class_v2/' not in sys.path and 'class_v2' not in sys.path:
    sys.path.insert(0, 'class_v2/')


__hooked = False
old__import__ = builtins.__import__


def hook_import():
    global __hooked

    if __hooked:
        return

    def _aap__import__(name, globals = None, locals = None, fromlist = (), level = 0):
        try:
            return old__import__(name, globals, locals, fromlist, level)

        except SyntaxError:
            # searching module in project.
            if level == 0 and str(name).strip() != '':
                panel_path = public.get_panel_path()
                pyfile = '{}.py'.format(str(name).strip().replace('.', '/'))

                realpath = os.path.join(panel_path, 'class', pyfile)
                cond = os.path.exists(realpath)

                if not cond:
                    realpath = os.path.join(panel_path, 'class_v2', pyfile)
                    cond = os.path.exists(realpath)

                if not cond:
                    realpath = os.path.join(panel_path, pyfile)
                    cond = os.path.exists(realpath)

                if cond:
                    try:
                        # public.print_log('Load project module: {} {} {} {}'.format(name, level, realpath, fromlist))

                        m = plugin_loader.get_module(realpath)

                        if fromlist is None or len(fromlist) == 0:
                            return m

                        for prop_name in fromlist:
                            prop = getattr(m, prop_name)

                            if globals is not None:
                                globals[prop_name] = prop

                            if locals is not None:
                                locals[prop_name] = prop

                        return m

                    except:
                        raise

            raise

    builtins.__import__ = _aap__import__

    __hooked = True
