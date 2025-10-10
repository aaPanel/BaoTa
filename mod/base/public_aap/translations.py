# Language translations
import os
import glob
import json
import public

translations = {}
login_translations = {}


# Load translations
def load_translations():
    # if len(translations.keys()) > 0:
    #     return translations

    # scan_pattern = '{}/BTPanel/static/vite/lang/*/*.json'.format(public.get_panel_path())

    # 获取设置语言 避免配置被覆盖
    path = "/www/server/panel/BTPanel/languages/language.pl"
    lang = ""
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as data:
            lang = data.read()

    key = 'en'
    filename = '/www/server/panel/BTPanel/languages/settings.json'
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                data = json.load(file)
                key = data['default']
            if lang != '':
                if key != lang:
                    data['default'] = lang
                    key = lang
                    with open(filename, 'w', encoding='utf-8') as file:
                        file.write(json.dumps(data, indent=4))

        except:
            pass

    scan_pattern_dir = '{}/BTPanel/static/vite/lang/{}'.format(public.get_panel_path(), key)
    if not os.path.exists(scan_pattern_dir):
        key = 'en'

    # 改获取用户设置的语言 没有使用默认英语
    scan_pattern = '{}/BTPanel/static/vite/lang/{}/*.json'.format(public.get_panel_path(), key)



    try:
        for path in glob.glob(scan_pattern):
            lan = os.path.basename(os.path.dirname(path))
            if lan not in translations:
                translations[lan] = {}
            with open(path, 'r') as fp:
                translations[lan].update(json.loads(fp.read()))
        # 只保留最新设置的语言
        translations2 = {k: v for k, v in translations.items() if k == key or k == translations.get(key)}
        return translations2
    except:
        public.print_log(public.get_error_info())

# 只返回登录语言包
def load_login_translations():
    # if len(login_translations.keys()) > 0:
    #     return login_translations

    scan_pattern = '{}/BTPanel/static/vite/lang/*/login.json'.format(public.get_panel_path())

    try:
        for path in glob.glob(scan_pattern):
            lan = os.path.basename(os.path.dirname(path))
            if lan not in login_translations:
                login_translations[lan] = {}
            with open(path, 'r') as fp:
                login_translations[lan].update(json.loads(fp.read()))

        return login_translations
    except:
        public.print_log(public.get_error_info())