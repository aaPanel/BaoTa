from typing import Optional


class BaseProjectCommon:
    setup_path = "/www/server/panel"
    _allow_mod_name = {
        "go", "java", "net", "nodejs", "other", "python", "proxy",
    }

    def get_project_mod_type(self) -> Optional[str]:
        _mod_name = self.__class__.__module__

        # "projectModel/javaModel.py" 的格式
        if "/" in _mod_name:
            _mod_name = _mod_name.replace("/", ".")
        if _mod_name.endswith(".py"):
            mod_name = _mod_name[:-3]
        else:
            mod_name = _mod_name

        # "projectModel.javaModel" 的格式
        if "." in mod_name:
            mod_name = mod_name.rsplit(".", 1)[1]

        if mod_name.endswith("Model"):
            return mod_name[:-5]
        if mod_name in self._allow_mod_name:
            return mod_name
        return None

    @property
    def config_prefix(self) -> Optional[str]:
        if getattr(self, "_config_prefix_cache", None) is not None:
            return getattr(self, "_config_prefix_cache")
        p_name = self.get_project_mod_type()
        if p_name == "nodejs":
            p_name = "node"

        if isinstance(p_name, str):
            p_name = p_name + "_"

        setattr(self, "_config_prefix_cache", p_name)
        return p_name

    @config_prefix.setter
    def config_prefix(self, prefix: str):
        setattr(self, "_config_prefix_cache", prefix)
