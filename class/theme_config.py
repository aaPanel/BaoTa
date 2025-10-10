#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主题配置管理模块

该模块提供主题配置的管理功能，包括：
- 配置文件的读取、验证和保存
- 新旧版本配置格式的转换
- 配置字段的验证和默认值处理
- 配置文件状态检查和初始化

作者: 宝塔面板开发团队
版本: 2.0.0 (优化版)
创建时间: 2025-09-15
"""

import json
import os
import re
import shutil
import tarfile
import tempfile
import urllib.parse
from typing import Dict, Any, Optional, Union, Tuple
from functools import wraps


def exception_handler(default_data=None):
    """统一异常处理装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except json.JSONDecodeError as e:
                return self.return_message(False, f'JSON解析错误: {str(e)}', default_data)
            except FileNotFoundError as e:
                return self.return_message(False, f'文件未找到: {str(e)}', default_data)
            except PermissionError as e:
                return self.return_message(False, f'权限错误: {str(e)}', default_data)
            except Exception as e:
                return self.return_message(False, f'{func.__name__}操作异常: {str(e)}', default_data)
        return wrapper
    return decorator


class FieldValidator:
    """简化的字段验证器"""
    
    def __init__(self, field_type=None, required=False, choices=None, pattern=None, min_val=None, max_val=None):
        self.field_type = field_type
        self.required = required
        self.choices = choices
        self.pattern = re.compile(pattern) if pattern else None
        self.min_val = min_val
        self.max_val = max_val
    
    def validate(self, value: Any) -> Tuple[bool, str]:
        """验证字段值"""
        # 检查必填字段
        if self.required and (value is None or value == ''):
            return False, '字段是必填的'
        
        # 空值且非必填，跳过验证
        if value is None or value == '':
            return True, ''
        
        # 类型转换和验证
        if self.field_type:
            value = self._convert_type(value)
            if not isinstance(value, self.field_type):
                return False, f'类型错误，期望 {self.field_type.__name__}'
        
        # 选择项验证
        if self.choices and value not in self.choices:
            return False, f'值不在允许的选择项中: {self.choices}'
        
        # 正则表达式验证
        if self.pattern and isinstance(value, str) and not self.pattern.match(value):
            return False, '值不匹配正则表达式模式'
        
        # 范围验证
        if self.min_val is not None and value < self.min_val:
            return False, f'值小于最小值 {self.min_val}'
        if self.max_val is not None and value > self.max_val:
            return False, f'值大于最大值 {self.max_val}'
        
        return True, ''
    
    def _convert_type(self, value):
        """类型转换"""
        if self.field_type == bool and isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'on']
        elif self.field_type == int and isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                pass
        return value


try:
    import public
except ImportError:
    class PublicCompat:
        @staticmethod
        def returnMsg(status, msg, data=None):
            result = {'status': status, 'msg': msg}
            if data is not None:
                result['data'] = data
            return result
    
    public = PublicCompat()


class ThemeConfigManager:
    """主题配置管理器 - 优化版"""
    
    # 默认配置常量
    DEFAULT_CONFIG = {
        "theme": {
            "preset": "light",
            "color": "#20a53a",
            "view": "default"
        },
        "logo": {
            "image": "/static/icons/logo-white.svg",
            "favicon": "/static/favicon.ico"
        },
        "sidebar": {
            "dark": True,
            "color": "#3c444d",
            "opacity": 100
        },
        "interface": {
            "rounded": "small",
            "is_show_bg": True,
            "bg_image": "/static/images/bg-default.png",
            "bg_image_opacity": 20,
            "content_opacity": 70,
            "shadow_color": "#000000",
            "shadow_opacity": 5
        },
        "home": {
            "overview_view": "default",
            "overview_size": 24
        },
        "login": {
            "is_show_logo": True,
            "logo": "/static/icons/logo-green.svg",
            "is_show_bg": False,
            "bg_image": "",
            "bg_image_opacity": 70,
            "content_opacity": 100
        }
    }
    
    # 字段验证器配置
    FIELD_VALIDATORS = {
        "theme.preset": FieldValidator(str, required=True, choices=["light", "dark"]),
        "theme.color": FieldValidator(str, required=True, pattern=r"^#[0-9a-fA-F]{3,6}$"),
        "theme.view": FieldValidator(str, required=True, choices=["default", "compact", "wide"]),
        "sidebar.dark": FieldValidator(bool, required=True),
        "sidebar.color": FieldValidator(str, required=True, pattern=r"^#[0-9a-fA-F]{3,6}$"),
        "sidebar.opacity": FieldValidator(int, required=True, min_val=0, max_val=100),
        "interface.rounded": FieldValidator(str, required=True, choices=["none", "small", "medium", "large"]),
        "interface.is_show_bg": FieldValidator(bool, required=True),
        "interface.bg_image_opacity": FieldValidator(int, required=True, min_val=0, max_val=100),
        "interface.content_opacity": FieldValidator(int, required=True, min_val=0, max_val=100),
        "interface.shadow_color": FieldValidator(str, required=True, pattern=r"^#[0-9a-fA-F]{3,6}$"),
        "interface.shadow_opacity": FieldValidator(int, required=True, min_val=0, max_val=100),
        "home.overview_view": FieldValidator(str, required=True, choices=["default", "grid", "list"]),
        "home.overview_size": FieldValidator(int, required=True, min_val=12, max_val=48),
        "login.is_show_logo": FieldValidator(bool, required=True),
        "login.is_show_bg": FieldValidator(bool, required=True),
        "login.bg_image_opacity": FieldValidator(int, required=True, min_val=0, max_val=100),
        "login.content_opacity": FieldValidator(int, required=True, min_val=0, max_val=100)
    }
    
    # 旧版本字段映射
    LEGACY_MAPPING = {
        "favicon": "logo.favicon",
        "dark": "theme.preset",  # 旧的dark字段映射到新的preset字段
        "show_login_logo": "login.is_show_logo",
        "show_login_bg_images": "login.is_show_bg",
        "login_logo": "login.logo",
        "login_bg_images": "login.bg_image",
        "login_bg_images_opacity": "login.bg_image_opacity",
        "login_content_opacity": "login.content_opacity",
        "show_main_bg_images": "interface.is_show_bg",
        "main_bg_images": "interface.bg_image",
        "main_bg_images_opacity": "interface.bg_image_opacity",
        "main_content_opacity": "interface.content_opacity",
        "main_shadow_color": "interface.shadow_color",
        "main_shadow_opacity": "interface.shadow_opacity",
        "menu_logo": "logo.image",
        "menu_bg_opacity": "sidebar.opacity",
        "sidebar_opacity": "sidebar.opacity",
        "theme_color": "sidebar.color",
        "home_state_font_size": "home.overview_size",
    }
    
    @staticmethod
    def return_message(status, msg, data=None):
        """统一的消息返回函数"""
        return {
            'msg': msg,
            'data': data if data is not None else {},
            'status': status
        }
    
    def __init__(self, config_file_path='/www/server/panel/data/panel_asset.json', auto_init=True):
        """初始化主题配置管理器"""
        self.config_file_path = config_file_path
        self.config_dir = os.path.dirname(self.config_file_path)
        self._path_cache = {}  # 路径缓存
        
        # 可选的自动初始化配置文件
        if auto_init:
            self._ensure_config_file()
    
    def _split_path(self, path: str) -> list:
        """分割路径并缓存结果"""
        if path not in self._path_cache:
            self._path_cache[path] = path.split('.')
        return self._path_cache[path]
    
    def _get_nested_value(self, data, path, default=None):
        """获取嵌套字典的值"""
        if not isinstance(data, dict):
            return default
        
        keys = self._split_path(path)
        current = data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError, AttributeError):
            return default
    
    def _set_nested_value(self, data, path, value):
        """设置嵌套字典的值"""
        keys = self._split_path(path)
        current = data
        
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _is_legacy_format(self, config):
        """检查配置是否为旧版本格式"""
        legacy_fields = set(self.LEGACY_MAPPING.keys())
        new_structure_keys = set(self.DEFAULT_CONFIG.keys())
        config_keys = set(config.keys())
        
        has_legacy_fields = bool(legacy_fields.intersection(config_keys))
        has_new_structure = bool(new_structure_keys.intersection(config_keys))
        
        return has_legacy_fields and not has_new_structure
    
    def _ensure_config_file(self):
        """确保配置文件存在"""
        if not os.path.exists(self.config_file_path):
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
    
    def validate_field(self, field_path: str, value: Any) -> Dict[str, Any]:
        """验证单个字段的值"""
        try:
            validator = self.FIELD_VALIDATORS.get(field_path)
            if not validator:
                return self.return_message(True, '字段验证通过', {'value': value})
            
            is_valid, error_msg = validator.validate(value)
            if not is_valid:
                return self.return_message(False, f'字段 {field_path} {error_msg}')
            
            return self.return_message(True, '字段验证通过', {'value': value})
        
        except Exception as e:
            return self.return_message(False, f"字段验证异常: {str(e)}")
    
    def detect_missing_fields(self, config):
        """检测配置中缺失的必要字段"""
        try:
            if not isinstance(config, dict):
                return self.return_message(False, '配置必须是字典类型')
            
            missing_fields = []
            
            def _check_nested_fields(default_dict, current_dict, path_prefix=''):
                """递归检查嵌套字段"""
                for key, default_value in default_dict.items():
                    current_path = f"{path_prefix}.{key}" if path_prefix else key
                    
                    if key not in current_dict:
                        missing_fields.append({
                            'path': current_path,
                            'default_value': default_value,
                            'type': type(default_value).__name__
                        })
                    elif isinstance(default_value, dict) and isinstance(current_dict.get(key), dict):
                        _check_nested_fields(default_value, current_dict[key], current_path)
            
            _check_nested_fields(self.DEFAULT_CONFIG, config)
            
            return self.return_message(True, f'检测到 {len(missing_fields)} 个缺失字段', {
                'missing_fields': missing_fields,
                'total_missing': len(missing_fields)
            })
        
        except Exception as e:
            return self.return_message(False, f'字段检测异常: {str(e)}')
    
    def auto_fill_missing_fields(self, config):
        """自动补充配置中缺失的必要字段"""
        try:
            if not isinstance(config, dict):
                return self.return_message(False, '配置必须是字典类型')
            
            import copy
            filled_config = copy.deepcopy(config)
            filled_count = 0
            filled_fields = []
            
            def _fill_nested_fields(default_dict, current_dict, path_prefix=''):
                """递归填充嵌套字段"""
                nonlocal filled_count
                
                for key, default_value in default_dict.items():
                    current_path = f"{path_prefix}.{key}" if path_prefix else key
                    
                    if key not in current_dict:
                        # 缺失字段，进行补充
                        current_dict[key] = copy.deepcopy(default_value)
                        filled_count += 1
                        filled_fields.append({
                            'path': current_path,
                            'value': default_value,
                            'type': type(default_value).__name__
                        })
                    elif isinstance(default_value, dict):
                        # 确保当前字段也是字典类型
                        if not isinstance(current_dict.get(key), dict):
                            current_dict[key] = {}
                        _fill_nested_fields(default_value, current_dict[key], current_path)
            
            _fill_nested_fields(self.DEFAULT_CONFIG, filled_config)
            
            message = f'成功补充 {filled_count} 个缺失字段' if filled_count > 0 else '无需补充字段'
            
            return self.return_message(True, message, {
                'config': filled_config,
                'filled_fields': filled_fields,
                'filled_count': filled_count
            })
        
        except Exception as e:
            return self.return_message(False, f'字段补充异常: {str(e)}')
    
    def validate_config(self, config):
        """验证配置数据"""
        try:
            import copy
            validated_config = copy.deepcopy(config)
            
            # 补充缺失的顶级字段
            missing_count = 0
            for key, default_value in self.DEFAULT_CONFIG.items():
                if key not in validated_config:
                    validated_config[key] = copy.deepcopy(default_value)
                    missing_count += 1
            
            # 验证关键字段
            critical_fields = ['theme.color', 'theme.view', 'sidebar.color']
            validation_fix_count = 0
            
            for field_path in critical_fields:
                value = self._get_nested_value(validated_config, field_path)
                if value is not None:
                    validation_result = self.validate_field(field_path, value)
                    if not validation_result["status"]:
                        default_value = self._get_nested_value(self.DEFAULT_CONFIG, field_path)
                        if default_value is not None:
                            self._set_nested_value(validated_config, field_path, default_value)
                            validation_fix_count += 1
            
            # 构建返回消息
            message_parts = []
            if missing_count > 0:
                message_parts.append(f"补充了 {missing_count} 个缺失的顶级字段")
            if validation_fix_count > 0:
                message_parts.append(f"修复了 {validation_fix_count} 个验证错误")
            if not message_parts:
                message_parts.append("配置验证通过")
            
            return self.return_message(True, "，".join(message_parts), validated_config)
        
        except Exception as e:
            return self.return_message(False, f'配置验证异常: {str(e)}', self.DEFAULT_CONFIG)
    
    def convert_legacy_config(self, legacy_config):
        """将旧版本配置转换为新版本配置"""
        try:
            if not isinstance(legacy_config, dict):
                return self.return_message(False, '旧版本配置必须是字典类型')
            
            import copy
            new_config = copy.deepcopy(self.DEFAULT_CONFIG)
            converted_count = 0
            
            for old_field, new_path in self.LEGACY_MAPPING.items():
                if old_field in legacy_config:
                    value = legacy_config[old_field]
                    if not (isinstance(value, str) and value.strip().lower() == "undefined"):
                        # 特殊处理 dark 字段到 preset 字段的转换
                        if old_field == "dark" and new_path == "theme.preset":
                            # 将布尔值转换为对应的预设字符串
                            if isinstance(value, bool):
                                preset_value = "dark" if value else "light"
                            elif isinstance(value, str):
                                # 处理字符串形式的布尔值
                                preset_value = "dark" if value.lower() in ['true', '1', 'yes', 'on'] else "light"
                            else:
                                # 默认为 light
                                preset_value = "light"
                            self._set_nested_value(new_config, new_path, preset_value)
                        else:
                            # 普通字段直接设置
                            self._set_nested_value(new_config, new_path, value)
                        converted_count += 1
            
            return self.return_message(True, f'成功转换 {converted_count} 个配置项', new_config)
        
        except Exception as e:
            return self.return_message(False, f'配置转换异常: {str(e)}')
    
    def get_legacy_format_config(self):
        """获取旧版本格式的配置"""
        try:
            get_result = self.get_config()
            if not get_result['status']:
                return self.return_message(False, f'获取当前配置失败: {get_result["msg"]}')
            
            new_config = get_result['data']
            legacy_config = {}
            converted_count = 0
            
            for old_field, new_path in self.LEGACY_MAPPING.items():
                value = self._get_nested_value(new_config, new_path)
                if value is not None:
                    legacy_config[old_field] = value
                    converted_count += 1
            
            return self.return_message(True, f'成功转换 {converted_count} 个配置项为旧格式', legacy_config)
        
        except Exception as e:
            return self.return_message(False, f'转换旧格式配置异常: {str(e)}')
    
    def check_config_file_status(self):
        """检查配置文件状态"""
        try:
            status_info = {
                'file_path': self.config_file_path,
                'exists': os.path.exists(self.config_file_path),
                'directory_exists': os.path.exists(self.config_dir),
                'is_readable': False,
                'is_writable': False,
                'file_size': 0,
                'is_valid_json': False
            }
            
            if not status_info['exists']:
                if status_info['directory_exists']:
                    status_info['is_writable'] = os.access(self.config_dir, os.W_OK)
                return self.return_message(True, '配置文件状态检查完成', status_info)
            
            # 文件存在时的检查
            status_info['is_readable'] = os.access(self.config_file_path, os.R_OK)
            status_info['is_writable'] = os.access(self.config_file_path, os.W_OK)
            status_info['file_size'] = os.path.getsize(self.config_file_path)
            
            try:
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                status_info['is_valid_json'] = True
            except (json.JSONDecodeError, IOError):
                status_info['is_valid_json'] = False
            
            return self.return_message(True, '配置文件状态检查完成', status_info)
        
        except Exception as e:
            return self.return_message(False, f'配置文件状态检查失败: {str(e)}')
    
    @exception_handler(default_data=None)
    def get_config(self):
        """获取当前的主题配置"""
        try:
            # 读取配置文件
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self.return_message(True, '使用默认配置', self.DEFAULT_CONFIG)
        
        # 处理旧版本配置
        if self._is_legacy_format(config_data):
            convert_result = self.convert_legacy_config(config_data)
            if convert_result['status']:
                config_data = convert_result['data']
                # 保存转换后的配置
                self.save_config(config_data, skip_validation=True)
        
        # 检查并补充 theme.preset 字段
        config_data = self._ensure_preset_field(config_data)
        
        # 验证并补充配置
        validation_result = self.validate_config(config_data)
        if validation_result['status']:
            validated_config = validation_result['data']
            # 如果配置有变更，保存更新
            if self._config_has_changes(config_data, validated_config):
                self.save_config(validated_config, skip_validation=True)
            return self.return_message(True, f'获取配置成功，{validation_result["msg"]}', validated_config)
        
        return self.return_message(False, validation_result['msg'], self.DEFAULT_CONFIG)
    
    def _config_has_changes(self, original_config, new_config):
        """检测配置是否发生了实际变更"""
        try:
            original_json = json.dumps(original_config, sort_keys=True, ensure_ascii=False)
            new_json = json.dumps(new_config, sort_keys=True, ensure_ascii=False)
            return original_json != new_json
        except Exception:
            return True
    
    def _ensure_preset_field(self, config):
        """确保theme.preset字段存在，如果不存在则使用theme.dark进行补充，然后移除旧版的dark字段"""
        try:
            import copy
            config_copy = copy.deepcopy(config)
            
            # 确保theme字段存在
            if 'theme' not in config_copy:
                config_copy['theme'] = {}
            
            # 检查preset字段是否存在
            if 'preset' not in config_copy['theme'] or config_copy['theme']['preset'] is None:
                # 检查是否存在dark字段
                if 'dark' in config_copy['theme']:
                    dark_value = config_copy['theme']['dark']
                    # 将dark字段转换为preset字段
                    if isinstance(dark_value, bool):
                        config_copy['theme']['preset'] = "dark" if dark_value else "light"
                    elif isinstance(dark_value, str):
                        # 处理字符串形式的布尔值
                        config_copy['theme']['preset'] = "dark" if dark_value.lower() in ['true', '1', 'yes', 'on'] else "light"
                    else:
                        # 默认为light
                        config_copy['theme']['preset'] = "light"
                else:
                    # 如果dark字段也不存在，使用默认值
                    config_copy['theme']['preset'] = "light"
            
            # 移除旧版的dark字段（如果存在）
            if 'dark' in config_copy['theme']:
                del config_copy['theme']['dark']
            
            return config_copy
        
        except Exception as e:
            # 如果处理过程中出现异常，返回原配置
            return config
    
    def save_config(self, config, skip_validation=False):
        """保存配置到文件"""
        try:
            if not config:
                return self.return_message(False, '配置数据不能为空')
            
            if isinstance(config, str):
                config = json.loads(config)
            
            if not skip_validation:
                validation_result = self.validate_config(config)
                if not validation_result["status"]:
                    return self.return_message(False, f'配置验证失败: {validation_result["msg"]}', validation_result.get("data", {}))
                config_to_save = validation_result["data"]
            else:
                config_to_save = config
            
            os.makedirs(self.config_dir, exist_ok=True)
            
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, ensure_ascii=False, indent=2)
            
            return self.return_message(True, '配置保存成功', config_to_save)
        
        except Exception as e:
            return self.return_message(False, f'配置保存失败: {str(e)}')
    
    def update_config(self, updates):
        """更新配置"""
        try:
            if not isinstance(updates, dict):
                return self.return_message(False, '更新数据必须是字典类型')
            
            get_result = self.get_config()
            if not get_result['status']:
                return self.return_message(False, f'获取当前配置失败: {get_result["msg"]}')
            
            current_config = get_result['data']
            
            # 应用更新
            for field_path, value in updates.items():
                # 检查是否为旧版本字段名
                if field_path in self.LEGACY_MAPPING:
                    field_path = self.LEGACY_MAPPING[field_path]
                
                self._set_nested_value(current_config, field_path, value)
            
            # 保存更新后的配置
            save_result = self.save_config(current_config)
            if save_result['status']:
                return self.return_message(True, '配置更新成功', save_result['data'])
            else:
                return self.return_message(False, f'配置保存失败: {save_result["msg"]}', save_result.get('data', {}))
        
        except Exception as e:
            return self.return_message(False, f'配置更新失败: {str(e)}')
    
    def initialize_config_file(self, force=False):
        """手动初始化配置文件"""
        try:
            if os.path.exists(self.config_file_path) and not force:
                return self.return_message(True, '配置文件已存在，无需初始化')
            
            os.makedirs(self.config_dir, exist_ok=True)
            
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
            
            action = '重新初始化' if force else '初始化'
            return self.return_message(True, f'配置文件已{action}，创建默认配置', self.DEFAULT_CONFIG)
        
        except Exception as e:
            return self.return_message(False, f'配置文件初始化失败: {str(e)}')
    
    # 导入导出功能相关方法
    
    def _get_path_fields(self, config):
        """获取配置中所有包含路径的字段"""
        path_fields = []
        
        def _extract_paths(data, prefix=''):
            """递归提取路径字段"""
            if isinstance(data, dict):
                for key, value in data.items():
                    current_path = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, str) and self._is_path_field(key, value):
                        path_fields.append({
                            'field_path': current_path,
                            'value': value,
                            'is_local': self._is_local_path(value)
                        })
                    elif isinstance(value, dict):
                        _extract_paths(value, current_path)
        
        _extract_paths(config)
        return path_fields
    
    def _is_path_field(self, field_name, value):
        """判断字段是否为路径字段"""
        path_indicators = ['image', 'logo', 'favicon', 'bg_image']
        return any(indicator in field_name.lower() for indicator in path_indicators) and isinstance(value, str) and value.strip()
    
    def _is_local_path(self, path):
        """判断是否为本地路径（非URL）"""
        if not path or not isinstance(path, str):
            return False
        
        # 检查是否为URL
        parsed = urllib.parse.urlparse(path)
        if parsed.scheme in ['http', 'https', 'ftp', 'ftps']:
            return False
        
        # 检查是否为相对路径或绝对路径
        return path.startswith('/') or not parsed.scheme
    
    def _get_full_path(self, relative_path, base_path=None):
        """获取完整的文件路径"""
        if not relative_path or not isinstance(relative_path, str):
            return None
        
        # 自动检测基础路径
        if base_path is None:
            # 优先使用生产环境路径
            production_base = '/www/server/panel/BTPanel'
            # 如果生产环境路径不存在，使用当前项目路径
            if not os.path.exists(production_base):
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(current_dir)
                base_path = os.path.join(project_root, 'BTPanel')
            else:
                base_path = production_base
        
        # 如果是系统绝对路径（不以/static开头），直接返回
        if os.path.isabs(relative_path) and not relative_path.startswith('/static'):
            return relative_path
        
        # 移除开头的斜杠并拼接基础路径
        clean_path = relative_path.lstrip('/')
        return os.path.join(base_path, clean_path)
    
    def _copy_file_to_temp(self, source_path, temp_dir, relative_path):
        """复制文件到临时目录"""
        try:
            if not os.path.exists(source_path):
                return False, f'源文件不存在: {source_path}'
            
            # 创建目标目录结构
            target_path = os.path.join(temp_dir, relative_path.lstrip('/'))
            target_dir = os.path.dirname(target_path)
            os.makedirs(target_dir, exist_ok=True)
            
            # 复制文件
            shutil.copy2(source_path, target_path)
            return True, target_path
        
        except Exception as e:
            return False, f'复制文件失败: {str(e)}'
    
    @exception_handler(default_data=None)
    def export_theme_config(self, export_path=None):
        """导出主题配置和相关文件"""
        try:
            # 获取当前配置
            config_result = self.get_config()
            if not config_result['status']:
                return self.return_message(False, f'获取配置失败: {config_result["msg"]}')
            
            config = config_result['data']
            
            # 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix='theme_export_')
            
            try:
                # 获取所有路径字段
                path_fields = self._get_path_fields(config)
                copied_files = []
                skipped_files = []
                
                # 复制本地路径的文件
                for field_info in path_fields:
                    if field_info['is_local']:
                        source_path = self._get_full_path(field_info['value'])
                        if source_path and os.path.exists(source_path):
                            success, result = self._copy_file_to_temp(
                                source_path, temp_dir, field_info['value']
                            )
                            if success:
                                copied_files.append({
                                    'field': field_info['field_path'],
                                    'original_path': field_info['value'],
                                    'source_path': source_path,
                                    'target_path': result
                                })
                            else:
                                skipped_files.append({
                                    'field': field_info['field_path'],
                                    'path': field_info['value'],
                                    'reason': result
                                })
                        else:
                            skipped_files.append({
                                'field': field_info['field_path'],
                                'path': field_info['value'],
                                'reason': '文件不存在'
                            })
                    else:
                        skipped_files.append({
                            'field': field_info['field_path'],
                            'path': field_info['value'],
                            'reason': 'URL地址，跳过处理'
                        })
                
                # 复制配置文件
                config_target = os.path.join(temp_dir, 'panel_asset.json')
                with open(config_target, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                
                # 获取实际使用的基础路径
                actual_base_path = self._get_full_path('static').replace('/static', '') if self._get_full_path('static') else '/www/server/panel/BTPanel'
                
                # 创建导出信息文件
                export_info = {
                    'export_time': __import__('datetime').datetime.now().isoformat(),
                    'config_file': 'panel_asset.json',
                    'copied_files': copied_files,
                    'skipped_files': skipped_files,
                    'total_files': len(copied_files),
                    'base_path': actual_base_path
                }
                
                info_file = os.path.join(temp_dir, 'export_info.json')
                with open(info_file, 'w', encoding='utf-8') as f:
                    json.dump(export_info, f, ensure_ascii=False, indent=2)
                
                # 打包文件
                if not export_path:
                    export_path = '/tmp/panel_theme.tar.gz'
                    # 如果文件已存在，先删除旧文件
                    if os.path.exists(export_path):
                        os.remove(export_path)
                
                with tarfile.open(export_path, 'w:gz') as tar:
                    tar.add(temp_dir, arcname='theme_config')
                
                return self.return_message(True, f'主题配置导出成功，共复制 {len(copied_files)} 个文件', {
                    'export_path': export_path,
                    'export_info': export_info
                })
            
            finally:
                # 清理临时目录
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
        
        except Exception as e:
            return self.return_message(False, f'导出失败: {str(e)}')
    
    @exception_handler(default_data=None)
    def import_theme_config(self, import_file_path, backup_existing=True):
        """导入主题配置和相关文件"""
        try:
            if not os.path.exists(import_file_path):
                return self.return_message(False, '导入文件不存在')
            
            if not tarfile.is_tarfile(import_file_path):
                return self.return_message(False, '导入文件不是有效的tar.gz格式')
            
            # 创建临时目录用于解压
            temp_dir = tempfile.mkdtemp(prefix='theme_import_')
            
            try:
                # 解压文件
                with tarfile.open(import_file_path, 'r:gz') as tar:
                    tar.extractall(temp_dir)
                
                # 查找解压后的主目录
                extracted_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
                if not extracted_dirs:
                    return self.return_message(False, '解压文件中未找到有效的配置目录')
                
                config_dir = os.path.join(temp_dir, extracted_dirs[0])
                
                # 检查必要文件
                config_file = os.path.join(config_dir, 'panel_asset.json')
                info_file = os.path.join(config_dir, 'export_info.json')
                
                if not os.path.exists(config_file):
                    return self.return_message(False, '导入文件中未找到配置文件 panel_asset.json')
                
                # 读取配置文件
                with open(config_file, 'r', encoding='utf-8') as f:
                    import_config = json.load(f)
                
                # 读取导出信息（如果存在）
                export_info = {}
                if os.path.exists(info_file):
                    with open(info_file, 'r', encoding='utf-8') as f:
                        export_info = json.load(f)
                
                # 备份现有配置
                backup_path = None
                if backup_existing and os.path.exists(self.config_file_path):
                    backup_path = f'{self.config_file_path}.backup_{__import__("time").strftime("%Y%m%d_%H%M%S")}'
                    shutil.copy2(self.config_file_path, backup_path)
                
                # 恢复文件
                restored_files = []
                failed_files = []
                # 使用动态基础路径检测
                base_path = self._get_full_path('static').replace('/static', '') if self._get_full_path('static') else '/www/server/panel/BTPanel'
                
                # 获取导入配置中的路径字段
                path_fields = self._get_path_fields(import_config)
                
                for field_info in path_fields:
                    if field_info['is_local']:
                        # 构建源文件路径（在临时目录中）
                        source_file = os.path.join(config_dir, field_info['value'].lstrip('/'))
                        
                        if os.path.exists(source_file):
                            # 构建目标路径
                            target_path = self._get_full_path(field_info['value'], base_path)
                            
                            try:
                                # 创建目标目录
                                target_dir = os.path.dirname(target_path)
                                os.makedirs(target_dir, exist_ok=True)
                                
                                # 复制文件
                                shutil.copy2(source_file, target_path)
                                restored_files.append({
                                    'field': field_info['field_path'],
                                    'path': field_info['value'],
                                    'target': target_path
                                })
                            
                            except Exception as e:
                                failed_files.append({
                                    'field': field_info['field_path'],
                                    'path': field_info['value'],
                                    'error': str(e)
                                })
                        else:
                            failed_files.append({
                                'field': field_info['field_path'],
                                'path': field_info['value'],
                                'error': '导入文件中不存在该文件'
                            })
                
                # 保存配置
                save_result = self.save_config(import_config)
                if not save_result['status']:
                    # 如果保存失败，恢复备份
                    if backup_path and os.path.exists(backup_path):
                        shutil.copy2(backup_path, self.config_file_path)
                    return self.return_message(False, f'配置保存失败: {save_result["msg"]}')
                
                return self.return_message(True, f'主题配置导入成功，恢复了 {len(restored_files)} 个文件', {
                    'restored_files': restored_files,
                    'failed_files': failed_files,
                    'backup_path': backup_path,
                    'export_info': export_info
                })
            
            finally:
                # 清理临时目录
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
        
        except Exception as e:
            return self.return_message(False, f'导入失败: {str(e)}')
    
    def validate_theme_file(self, import_file_path):
        """验证导入文件的有效性"""
        try:
            if not os.path.exists(import_file_path):
                return self.return_message(False, '导入文件不存在')
            
            if not tarfile.is_tarfile(import_file_path):
                return self.return_message(False, '文件不是有效的tar.gz格式')
            
            # 创建临时目录用于验证
            temp_dir = tempfile.mkdtemp(prefix='theme_validate_')
            
            try:
                # 解压文件进行验证
                with tarfile.open(import_file_path, 'r:gz') as tar:
                    tar.extractall(temp_dir)
                
                # 查找解压后的主目录
                extracted_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
                if not extracted_dirs:
                    return self.return_message(False, '压缩文件中未找到有效的配置目录')
                
                config_dir = os.path.join(temp_dir, extracted_dirs[0])
                
                # 检查必要文件
                config_file = os.path.join(config_dir, 'panel_asset.json')
                info_file = os.path.join(config_dir, 'export_info.json')
                
                if not os.path.exists(config_file):
                    return self.return_message(False, '压缩文件中未找到配置文件 panel_asset.json')
                
                # 验证配置文件格式
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        import_config = json.load(f)
                except json.JSONDecodeError:
                    return self.return_message(False, '配置文件格式无效')
                
                # 读取导出信息
                export_info = {}
                if os.path.exists(info_file):
                    try:
                        with open(info_file, 'r', encoding='utf-8') as f:
                            export_info = json.load(f)
                    except json.JSONDecodeError:
                        pass  # 导出信息文件可选
                
                # 验证配置结构
                validation_result = self.validate_config(import_config)
                if not validation_result['status']:
                    return self.return_message(False, f'配置验证失败: {validation_result["msg"]}')
                
                # 统计文件信息
                path_fields = self._get_path_fields(import_config)
                available_files = []
                missing_files = []
                
                for field_info in path_fields:
                    if field_info['is_local']:
                        source_file = os.path.join(config_dir, field_info['value'].lstrip('/'))
                        if os.path.exists(source_file):
                            file_size = os.path.getsize(source_file)
                            available_files.append({
                                'field': field_info['field_path'],
                                'path': field_info['value'],
                                'size': file_size
                            })
                        else:
                            missing_files.append({
                                'field': field_info['field_path'],
                                'path': field_info['value']
                            })
                
                return self.return_message(True, '导入文件验证通过', {
                    'config': import_config,
                    'export_info': export_info,
                    'available_files': available_files,
                    'missing_files': missing_files,
                    'total_available': len(available_files),
                    'total_missing': len(missing_files)
                })
            
            finally:
                # 清理临时目录
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
        
        except Exception as e:
            return self.return_message(False, f'验证失败: {str(e)}')
    
    def get_export_file_info(self, export_file_path):
        """获取导出文件的详细信息"""
        try:
            if not os.path.exists(export_file_path):
                return self.return_message(False, '文件不存在')
            
            file_info = {
                'file_path': export_file_path,
                'file_size': os.path.getsize(export_file_path),
                'is_valid_tar': tarfile.is_tarfile(export_file_path)
            }
            
            if not file_info['is_valid_tar']:
                return self.return_message(False, '不是有效的tar.gz文件', file_info)
            
            # 获取压缩文件内容列表
            with tarfile.open(export_file_path, 'r:gz') as tar:
                file_info['contents'] = tar.getnames()
                file_info['total_files'] = len(file_info['contents'])
            
            # 验证文件内容
            validation_result = self.validate_theme_file(export_file_path)
            if validation_result['status']:
                file_info.update(validation_result['data'])
            
            return self.return_message(True, '文件信息获取成功', file_info)
        
        except Exception as e:
            return self.return_message(False, f'获取文件信息失败: {str(e)}')
    
    def test_path_detection(self):
        """测试路径检测和文件存在性检查"""
        try:
            # 获取当前配置
            config_result = self.get_config()
            if not config_result['status']:
                return self.return_message(False, f'获取配置失败: {config_result["msg"]}')
            
            config = config_result['data']
            
            # 检测基础路径
            base_path = self._get_full_path('static').replace('/static', '') if self._get_full_path('static') else '/www/server/panel/BTPanel'
            
            # 获取所有路径字段
            path_fields = self._get_path_fields(config)
            
            test_results = {
                'base_path': base_path,
                'base_path_exists': os.path.exists(base_path),
                'path_fields': [],
                'summary': {
                    'total_fields': len(path_fields),
                    'local_fields': 0,
                    'url_fields': 0,
                    'existing_files': 0,
                    'missing_files': 0
                }
            }
            
            for field_info in path_fields:
                field_result = {
                    'field_path': field_info['field_path'],
                    'value': field_info['value'],
                    'is_local': field_info['is_local'],
                    'full_path': None,
                    'exists': False
                }
                
                if field_info['is_local']:
                    test_results['summary']['local_fields'] += 1
                    full_path = self._get_full_path(field_info['value'])
                    field_result['full_path'] = full_path
                    if full_path and os.path.exists(full_path):
                        field_result['exists'] = True
                        test_results['summary']['existing_files'] += 1
                    else:
                        test_results['summary']['missing_files'] += 1
                else:
                    test_results['summary']['url_fields'] += 1
                
                test_results['path_fields'].append(field_result)
            
            return self.return_message(True, '路径检测测试完成', test_results)
        
        except Exception as e:
            return self.return_message(False, f'路径检测测试失败: {str(e)}')
    