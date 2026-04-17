import json
import os
import subprocess
from typing import Any, Dict, List, Optional
import public

plugin_registry: Dict[str, Dict[str, Any]] = {}


def scan_plugins(dir_path: str) -> List[Dict[str, Any]]:
    global plugin_registry
    plugin_registry = {}
    plugins: List[Dict[str, Any]] = []
    for root, _, files in os.walk(dir_path or ""):
        for fname in files:
            path = os.path.join(root, fname)
            try:
                meta = get_metadata(path)
            except Exception as err:
                public.print_log("插件无效:", path, "错误:", err)
                continue
            meta["path"] = path
            plugins.append(meta)
            plugin_registry[meta.get("name", "")] = meta
    return plugins


def get_metadata(path: str) -> Dict[str, Any]:
    req = {"action": "get_metadata", "params": {}}
    data = json.dumps(req).encode("utf-8")
    try:
        proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        out, _ = proc.communicate(input=data)
        rc = proc.returncode
        if rc != 0:
            raise RuntimeError(f"运行失败: return code {rc}")
    except Exception as e:
        raise RuntimeError(f"运行失败: {e}")
    try:
        payload = json.loads(out.decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"输出无效: {e}")
    status = payload.get("status")
    if status != "success":
        raise RuntimeError(f"插件响应错误: {payload.get('message', '')}")
    result = payload.get("result") or {}
    if not isinstance(result, dict):
        raise RuntimeError("响应格式无效")
    if not result:
        raise RuntimeError("响应结果为空")
    config = result.get("config", [])
    if config and isinstance(config, list):
        for c in config:
            if not isinstance(c, dict):
                raise RuntimeError("配置参数格式无效")
            if not c.get("name") or not c.get("description") or not c.get("type"):
                raise RuntimeError("配置参数缺失字段")
    else:
        result["config"] = []

    actions_payload = result.get("actions") or []
    actions = []
    for a in actions_payload:
        if not isinstance(a, dict):
            raise RuntimeError("操作格式无效")
        if not a.get("name") or not a.get("description"):
            raise RuntimeError("操作缺失字段")
        params = a.get("params", [])
        if params and isinstance(params, list):
            for p in params:
                if not isinstance(p, dict):
                    raise RuntimeError("操作参数格式无效")
                if not p.get("name") or not p.get("description") or not p.get("type"):
                    raise RuntimeError("操作参数缺失字段")
        else:
            params = []
        actions.append({
            "name": a.get("name", ""),
            "description": a.get("description", ""),
            "params": params,
        })
    meta = {
        "name": result.get("name", ""),
        "description": result.get("description", ""),
        "version": result.get("version", ""),
        "author": result.get("author", ""),
        "actions": actions,
        "config": result.get("config") or None,
        "path": "",
    }
    if not meta["name"] or len(meta["actions"]) == 0:
        raise RuntimeError("元数据缺失")
    return meta


def call_plugin(name: str, action: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    resp = try_call_plugin(name, action, params)
    if resp.get("status") == "error" and resp.get("message") in {"插件未找到", "插件不支持该 action"}:
        try:
            get_plugins()
        except Exception as scan_err:
            return {"status": "error", "message": f"插件刷新失败: {scan_err}", "result": {}}
        return try_call_plugin(name, action, params)
    return resp


def try_call_plugin(name: str, action: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    plugin = plugin_registry.get(name)
    if not plugin:
        return {"status": "error", "message": "插件未找到", "result": {}}
    found = any((a.get("name") == action) for a in plugin.get("actions", []))
    if not found:
        return {"status": "error", "message": "插件不支持该 action", "result": {}}
    req = {"action": action, "params": params or {}}
    try:
        proc = subprocess.Popen(
            [plugin.get("path", "")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        req_bytes = json.dumps(req).encode("utf-8")
        assert proc.stdin is not None
        proc.stdin.write(req_bytes)
        proc.stdin.close()
        assert proc.stdout is not None
        resp_bytes = proc.stdout.read()
        rc = proc.wait()
        if rc != 0:
            raise RuntimeError(f"运行失败: return code {rc}")
    except Exception as e:
        return {"status": "error", "message": str(e), "result": {}}
    try:
        payload = json.loads(resp_bytes.decode("utf-8"))
    except Exception as e:
        return {"status": "error", "message": f"解析插件响应失败: {e}", "result": {}}
    if payload.get("status") != "success":
        return {"status": "error", "message": payload.get("message", ""), "result": payload.get("result") or {}}
    return {"status": payload.get("status", ""), "message": payload.get("message", ""), "result": payload.get("result") or {}}


def get_plugins() -> List[Dict[str, Any]]:
    plugin_dir = "/www/server/deploy_plugin"
    return scan_plugins(plugin_dir)


def get_actions(plugin_name: str) -> List[Dict[str, Any]]:
    get_plugins()
    meta = plugin_registry.get(plugin_name)
    if not meta:
        return []
    return meta.get("actions", [])