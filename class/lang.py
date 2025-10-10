#coding: utf-8
import os
import json
import public

class Lang:

    def __init__(self):
        pass
    # todo 改languages 放置路径
    def getLanguagePath(self):
        '''
            @name 获取语言包路径
            @returns {string}
        '''
        # return os.path.join(os.path.dirname(__file__),'..','languages')
        return '/www/server/panel/BTPanel/languages'

    def getLanguage(self):
        '''
            @name 获取当前语言
            @returns {string}
        '''
        language_path = self.getLanguagePath()
        settings_file = os.path.join(language_path,'settings.json')
        default_lang = 'en'

        # 获取已设置语言 避免覆盖
        path1 = "/www/server/panel/BTPanel/languages/language.pl"
        if os.path.exists(path1):
            with open(path1, 'r', encoding='utf-8') as data1:
                lang = data1.read()
                if lang:
                    default_lang = lang


        if not os.path.exists(settings_file):
            return default_lang
        with open(settings_file,'r',encoding='utf-8') as file:
            data = file.read()
            if not data:
                return default_lang
            settings = json.loads(data)
            if not settings.get('languages', None):
                return default_lang
            return settings.get('default',default_lang)
        
    def getLang(self,content,*args):
        '''
            @name 多语言渲染
            @param {string} content - 内容
            @param {any[]} args - 参数
            @returns {string}
            @example lang('Hello {}', 'World')
            @example lang('Hello {} {}', 'World', '!')
            @example lang('Hello')
        '''
        hash = public.md5(content)
        lang = self.getLanguage()
        lang_file = os.path.join(self.getLanguagePath(),lang,'server.json')
        lang_data = {}

        if os.path.exists(lang_file):
            with open(lang_file,'r',encoding='utf-8') as file:
                lang_data = json.loads(file.read())
        
        lang_content = content
        if lang_data.get(hash):
            lang_content = lang_data[hash]
        if len(args) > 0:
            lang_content = lang_content.format(*args)
        return lang_content
    
    def setLanguage(self,lang):
        '''
            @name 设置语言
            @param {string} lang - 语言
        '''
        settings_file = os.path.join(self.getLanguagePath(),'settings.json')
        settings = {}
        if os.path.exists(settings_file):
            with open(settings_file,'r',encoding='utf-8') as file:
                settings = json.loads(file.read())
        settings['default'] = lang
        with open(settings_file,'w',encoding='utf-8') as file:
            file.write(json.dumps(settings,indent=4))
    
    def getClientLang(self):
        '''
            @name 获取客户端语言
            @returns {string}
        '''
        lang = self.getLanguage()
        lang_file = os.path.join(self.getLanguagePath(),lang,'client.json')
        lang_data = {}
        if os.path.exists(lang_file):
            with open(lang_file,'r',encoding='utf-8') as file:
                lang_data = json.loads(file.read())
        return lang_data



# JS版
# /**
# * @name 多语言渲染
# * @param {string} content - 内容
# * @param {any[]} args - 参数
# * @returns {string}
# * @example lang('Hello {}', 'World')
# * @example lang('Hello {} {}', 'World', '!')
# * @example lang('Hello')
# */
# lang(content,...args){
# let hash = this.md5(content);

# // 获取语言包
# let lang = this.get_language();
# let lang_file = path.resolve(this.get_language_path(), lang , 'server.json');
# let lang_data = {};
# if(fs.existsSync(lang_file)) {
#     lang_data = JSON.parse(this.read_file(lang_file));
# }

# // 尝试从语言包中获取内容
# let lang_content = content;
# if(lang_data[hash]){
#     lang_content = lang_data[hash];
# }

# // 替换参数
# if(args.length > 0){
#     lang_content = lang_content.replace(/{}/g, function() {
#         return args.shift();
#     });
# }

# // 返回内容
# return lang_content;
# }