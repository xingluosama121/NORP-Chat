import os
import sys
import json
import base64
import threading
import time
import re
from pathlib import Path
from anthropic import Anthropic
from typing import Optional, List, Dict, Any, Generator
from datetime import datetime

import webview
from openai import OpenAI
import win32crypt
import keyring

KEYRING_SERVICE = "dschat"
KEYRING_USER = "api_key"


LOCALAPPDATA = os.environ.get('LOCALAPPDATA', '')
if not LOCALAPPDATA:
    LOCALAPPDATA = os.getcwd()
APP_DIR = os.path.join(LOCALAPPDATA, 'dschat')
PATH_DIR = os.path.join(APP_DIR, 'path')
MEMORY_DIR = os.path.join(APP_DIR, 'memory')
BASE_ENV_FILE = os.path.join(APP_DIR, 'base.env')
CONFIG_FILE = os.path.join(APP_DIR, 'config.json')
MEMORY_FILE = os.path.join(MEMORY_DIR, 'memory.json')

for d in [APP_DIR, PATH_DIR, MEMORY_DIR]:
    Path(d).mkdir(parents=True, exist_ok=True)

DEFAULT_CONFIG = {
    "language": "zh_Cn",
    "model": "deepseek-v4-flash",
    "encryption_method": "win32crypt",
    "think": "关",
    "memory": False,
    "web_search": False,
    "temperature": 1.0,
    "max_tokens": 32767,
    "logprobs": False,
    "top_logprobs": 0,
    "show_reasoning": True,
    "json_mode": False,
    "stop_sequences": "",
    "user_id": "",
    "memory_mode": "full",
    "max_rounds": 10,
    "advanced_enabled": False,
    "api_base": "https://api.deepseek.com",
    "custom_model": "",
}

LANG_STRINGS = {
    "zh_Cn": {
        "title": "NORP API ",
        "about": "关于",
        "send": "发送",
        "stop": "停止",
        "settings": "设置",
        "change_key": "更换密钥",
        "clear_memory": "清除记忆",
        "file_upload": "上传",
        "language_label": "语言",
        "model_select": "模型",
        "think_label": "思考强度",
        "memory_label": "开启记忆 (Beta)",
        "web_search_label": "联网搜索",
        "temperature_label": "温度",
        "max_tokens_label": "最大输出长度",
        "logprobs_label": "返回对数概率",
        "top_logprobs_label": "Top对数概率个数",
        "show_reasoning_label": "显示思考过程",
        "json_mode_label": "JSON输出模式",
        "stop_sequences_label": "停止序列 (逗号分隔)",
        "user_id_label": "用户标识",
        "memory_mode_label": "记忆模式",
        "max_rounds_label": "记忆轮数",
        "memory_mode_full": "完整",
        "memory_mode_summary": "精简 (摘要)",
        "confirm": "确定",
        "cancel": "取消",
        "settings_saved": "设置已保存",
        "file_too_large": "文件过大 (最大10MB)",
        "file_unsupported": "不支持的文件格式",
        "advanced_enabled_label": "启用高级设置",
        "input_placeholder": "输入消息... (Enter发送, Ctrl+Enter换行)",
        "generation_stopped": "已停止生成",
        "load_memory": "已加载记忆",
        "no_reply": "(助手没有回复)",
        "reasoning_title": "思考过程",
        "stopped": "已停止",
        "loading_text": "加载中，请稍候...",
        "encryption_method_label": "密钥存储方式",
        "refresh_text": "刷新文本",
        "reset_page": "重置",
        "drop_hint": "拖入文件或点击选择",
        "send_files": "已发送 ({count} 个文件)",
        "file_too_large_msg": "文件过大: {name} (最大10MB)",
        "unsupported_format": "不支持: {name} (.{ext})",
        "read_error": "读取失败: {name} - {error}",
        "added_files": "已添加 {count} 个文件",
        "file_removed": "已移除文件",
        "no_file_or_text": "请选择文件或输入文本",
        "copy_success": "已复制",
        "reset_confirm": "确定重置页面吗？",
        "reset_done": "页面已重置",
        "config_loaded": "配置已加载",
        "config_saved": "设置已保存",
        "language_changed_restart": "语言已更改，需要重启程序生效。是否立即重启？",
        "memory_prefix": "本文档为用户上一轮的记忆，请不要回复关于该文档的任何内容。\n",
        "api_base_label": "API 地址",
        "api_base_placeholder": "例如: https://api.deepseek.com",
        "fetch_models_btn": "获取模型列表",
        "fetch_models_success": "已获取 {count} 个模型",
        "fetch_models_error": "获取模型列表失败: {error}",
        "api_key_required_for_models": "请先设置有效的 API 密钥",
        "balance_deepseek_only": "余额查询仅支持 DeepSeek 官方地址",
        "custom_model_label": "自定义模型名称（留空则使用下拉选择）",
    },
    "en": {
        "title": "NORP API ",
        "about": "About",
        "send": "Send",
        "stop": "Stop",
        "settings": "Settings",
        "change_key": "Change Key",
        "clear_memory": "Clear Memory",
        "file_upload": "Upload",
        "language_label": "Language",
        "model_select": "Model",
        "think_label": "Reasoning Effort",
        "memory_label": "Enable Memory (Beta)",
        "encryption_method_label": "Key Storage Method",
        "web_search_label": "Web Search",
        "temperature_label": "Temperature",
        "max_tokens_label": "Max Tokens",
        "logprobs_label": "Logprobs",
        "top_logprobs_label": "Top Logprobs",
        "show_reasoning_label": "Show Reasoning",
        "json_mode_label": "JSON Mode",
        "stop_sequences_label": "Stop Sequences (comma)",
        "user_id_label": "User ID",
        "memory_mode_label": "Memory Mode",
        "max_rounds_label": "Max Rounds",
        "memory_mode_full": "Full",
        "memory_mode_summary": "Summary",
        "confirm": "Confirm",
        "cancel": "Cancel",
        "settings_saved": "Settings saved",
        "file_too_large": "File too large (max 10MB)",
        "file_unsupported": "Unsupported format",
        "advanced_enabled_label": "Enable Advanced",
        "input_placeholder": "Type message... (Enter to send, Ctrl+Enter new line)",
        "generation_stopped": "Generation stopped",
        "load_memory": "Memory loaded",
        "no_reply": "(No reply)",
        "reasoning_title": "Reasoning",
        "stopped": "Stopped",
        "loading_text": "Loading...",
        "refresh_text": "Refresh",
        "reset_page": "Reset",
        "drop_hint": "Drop files or click to select",
        "send_files": "Sent ({count} files)",
        "file_too_large_msg": "File too large: {name} (max 10MB)",
        "unsupported_format": "Unsupported: {name} (.{ext})",
        "read_error": "Read error: {name} - {error}",
        "added_files": "Added {count} files",
        "file_removed": "File removed",
        "no_file_or_text": "Select a file or enter text",
        "copy_success": "Copied",
        "reset_confirm": "Reset the page?",
        "reset_done": "Page reset",
        "config_loaded": "Config loaded",
        "config_saved": "Settings saved",
        "language_changed_restart": "Language changed. Restart to apply?",
        "memory_prefix": "This document is the memory from your previous session. Do not reply to this document.\n",
        "api_base_label": "API Base URL",
        "api_base_placeholder": "e.g. https://api.deepseek.com",
        "fetch_models_btn": "Fetch Models",
        "fetch_models_success": "Fetched {count} models",
        "fetch_models_error": "Failed to fetch models: {error}",
        "api_key_required_for_models": "Please set a valid API key first",
        "balance_deepseek_only": "Balance query only supports DeepSeek official endpoint",
        "custom_model_label": "Custom model name (leave empty to use dropdown)",
    }
}

def encrypt_text(text: str) -> bytes:
    encrypted = win32crypt.CryptProtectData(text.encode('utf-8'), None, None, None, None, 0)
    return base64.b64encode(encrypted)

def decrypt_text(encrypted_b64: bytes) -> str:
    encrypted = base64.b64decode(encrypted_b64)
    decrypted = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)
    return decrypted[1].decode('utf-8')

def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any]):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def get_api_key_from_storage() -> Optional[str]:
    config = load_config()
    method = config.get('encryption_method', 'win32crypt')
    if method == "keyring":
        return keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
    else:
        if not os.path.exists(BASE_ENV_FILE):
            return None
        with open(BASE_ENV_FILE, 'rb') as f:
            encrypted_b64 = f.read()
        return decrypt_text(encrypted_b64)

def save_api_key(api_key: str):
    config = load_config()
    method = config.get('encryption_method', 'win32crypt')
    if method == "keyring":
        keyring.set_password(KEYRING_SERVICE, KEYRING_USER, api_key)
        if os.path.exists(BASE_ENV_FILE):
            os.remove(BASE_ENV_FILE)
    else:
        encrypted = encrypt_text(api_key)
        with open(BASE_ENV_FILE, 'wb') as f:
            f.write(encrypted)

def validate_api_key(api_key: str, base_url: str = "https://api.deepseek.com") -> bool:
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        client.models.list()
        return True
    except Exception:
        return False

def extract_text_from_file(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext in ['.txt', '.py', '.json', '.csv', '.css', '.html', '.md']:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    elif ext == '.pdf':
        try:
            import PyPDF2
        except ImportError:
            raise Exception("PyPDF2 not installed")
        text = []
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text() or '')
        return '\n'.join(text)
    elif ext == '.docx':
        try:
            import docx
        except ImportError:
            raise Exception("python-docx not installed")
        d = docx.Document(file_path)
        return '\n'.join([p.text for p in d.paragraphs])
    elif ext == '.xlsx':
        try:
            import openpyxl
        except ImportError:
            raise Exception("openpyxl not installed")
        wb = openpyxl.load_workbook(file_path, data_only=True)
        text = []
        for sheet in wb.worksheets:
            for row in sheet.iter_rows(values_only=True):
                text.append('\t'.join([str(cell) if cell is not None else '' for cell in row]))
        return '\n'.join(text)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def call_deepseek_api_sync(
    api_key: str,
    messages: List[Dict],
    model: str = "deepseek-v4-flash",
    temperature: float = 0.7,
    max_tokens: int = 32767,
    base_url: str = "https://api.deepseek.com",
) -> str:
    client = OpenAI(api_key=api_key, base_url=base_url)
    params = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    try:
        response = client.chat.completions.create(**params)
        return response.choices[0].message.content or ""
    except Exception as e:
        raise Exception(f"API call failed: {str(e)}")

def call_deepseek_api_stream(
    api_key: str,
    messages: List[Dict],
    model: str,
    think_level: str,
    enable_web_search: bool = False,
    stop_event=None,
    base_url: str = "https://api.deepseek.com",
    **kwargs
) -> Generator[str, None, None]:
    use_anthropic = enable_web_search and base_url in ("https://api.deepseek.com", "https://api.deepseek.com/")
    if use_anthropic:
        client = Anthropic(api_key=api_key, base_url="https://api.deepseek.com/anthropic")
        anthropic_messages = []
        system_prompt = ""
        for m in messages:
            if m["role"] == "system":
                system_prompt += m["content"] + "\n"
            elif m["role"] in ("user", "assistant"):
                anthropic_messages.append({
                    "role": m["role"],
                    "content": m["content"]
                })
        tools = [{"type": "web_search_20250305", "name": "web_search"}] if enable_web_search else None
        effort_map = {"低": "low", "中": "medium", "高": "max"}
        reasoning_effort = effort_map.get(think_level, "high") if think_level != "关" else None
        thinking_param = {"type": "enabled"} if reasoning_effort is not None else None
        output_config_param = {"effort": reasoning_effort} if reasoning_effort is not None else None

        try:
            with client.messages.stream(
                model=model,
                max_tokens=kwargs.get('max_tokens', 32767),
                system=system_prompt.strip() or "You are a helpful assistant.",
                messages=anthropic_messages,
                tools=tools,
                thinking=thinking_param,
                output_config=output_config_param,
                temperature=kwargs.get('temperature') if think_level == "关" else None,
            ) as stream:
                tool_uses = []
                for event in stream:
                    if stop_event and stop_event.is_set():
                        try:
                            stream.close()
                        except Exception:
                            pass
                        break
                    if event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            tool_uses.append({
                                "id": event.content_block.id,
                                "name": event.content_block.name,
                                "input": event.content_block.input
                            })
                    elif event.type == "content_block_delta":
                        if hasattr(event.delta, 'thinking'):
                            yield f"__REASONING__:{event.delta.thinking}"
                        elif hasattr(event.delta, 'text'):
                            yield event.delta.text
                    elif event.type == "message_stop":
                        usage = event.message.usage
                        yield f"__USAGE__:{usage.input_tokens},{usage.output_tokens}"
            if tool_uses:
                tool_messages = anthropic_messages.copy()
                for tu in tool_uses:
                    if tu["name"] == "web_search":
                        query = tu["input"].get("query", "")
                        if query:
                            search_result = f"关于「{query}」的搜索结果：今天南京天气晴朗，气温22-28°C。"
                            tool_messages.append({
                                "role": "user",
                                "content": [{
                                    "type": "tool_result",
                                    "tool_use_id": tu["id"],
                                    "content": search_result
                                }]
                            })
                with client.messages.stream(
                    model=model,
                    max_tokens=kwargs.get('max_tokens', 32767),
                    system=system_prompt.strip() or "You are a helpful assistant.",
                    messages=tool_messages,
                    tools=None,
                    thinking=thinking_param,
                    output_config=output_config_param,
                    temperature=kwargs.get('temperature') if think_level == "关" else None,
                ) as stream2:
                    for event in stream2:
                        if stop_event and stop_event.is_set():
                            try:
                                stream2.close()
                            except Exception:
                                pass
                            break
                        if event.type == "content_block_delta":
                            if hasattr(event.delta, 'thinking'):
                                yield f"__REASONING__:{event.delta.thinking}"
                            elif hasattr(event.delta, 'text'):
                                yield event.delta.text
                        elif event.type == "message_stop":
                            usage = event.message.usage
                            yield f"__USAGE__:{usage.input_tokens},{usage.output_tokens}"
        except Exception as e:
            yield f"__ERROR__:{str(e)}"
        return

    # OpenAI 兼容模式
    client = OpenAI(api_key=api_key, base_url=base_url)
    params = {
        "model": model,
        "messages": messages,
        "stream": True,
    }
    if kwargs.get('temperature') is not None:
        params["temperature"] = kwargs['temperature']
    if kwargs.get('max_tokens'):
        params["max_tokens"] = kwargs['max_tokens']
    if kwargs.get('stop_sequences'):
        stops = [s.strip() for s in kwargs['stop_sequences'].split(',') if s.strip()]
        if stops:
            params["stop"] = stops
    if kwargs.get('user_id'):
        params["user"] = kwargs['user_id']
    if kwargs.get('json_mode'):
        params["response_format"] = {"type": "json_object"}

    if enable_web_search:
        params["tools"] = [{
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the internet for real-time information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query."}
                    },
                    "required": ["query"]
                }
            }
        }]

    if think_level == "关":
        params["extra_body"] = {"thinking": {"type": "disabled"}}
        if kwargs.get('logprobs'):
            params["logprobs"] = True
            if kwargs.get('top_logprobs', 0) > 0:
                params["top_logprobs"] = kwargs['top_logprobs']
    else:
        effort_map = {"低": "low", "中": "medium", "高": "max"}
        effort = effort_map.get(think_level, "max")
        params["extra_body"] = {"thinking": {"type": "enabled"}, "reasoning_effort": effort}
        params.pop('temperature', None)
        params.pop('logprobs', None)
        params.pop('top_logprobs', None)

    try:
        response = client.chat.completions.create(**params)
        for chunk in response:
            delta = chunk.choices[0].delta
            reasoning = getattr(delta, 'reasoning_content', None)
            if reasoning:
                yield f"__REASONING__:{reasoning}"
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    if tc.function.name == "web_search":
                        try:
                            args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                            query = args.get("query", "")
                            if query:
                                search_result = f"关于「{query}」的搜索结果：请查看相关网站获取准确信息。"
                                yield f"__TOOL_RESULT__:{search_result}"
                        except json.JSONDecodeError:
                            continue
            if delta.content:
                yield delta.content
    except Exception as e:
        status_code = None
        if hasattr(e, 'status_code'):
            status_code = e.status_code
        elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
            status_code = e.response.status_code
        error_map = {
            400: "请求格式错误，请检查参数",
            401: "认证失败，请检查API密钥",
            402: "账户余额不足，请充值",
            422: "参数错误，请检查请求参数",
            429: "请求速率达到上限，请稍后再试",
            500: "服务器内部故障，请稍后重试",
            503: "服务器繁忙，请稍后重试",
        }
        if status_code in error_map:
            yield f"__ERROR__:{status_code}|{error_map[status_code]}"
        else:
            yield f"__ERROR__:{str(e)}"

class DeepSeekWebViewApp:
    def migrate_encryption(self, new_method: str):
        old_key = self.api_key or get_api_key_from_storage()
        if not old_key:
            return
        self.config['encryption_method'] = new_method
        save_api_key(old_key)

    def get_models_with_base(self, base_url: str):
        if not self.api_key:
            return {"error": self.strings.get('api_key_required_for_models', '请先设置 API 密钥')}
        try:
            client = OpenAI(api_key=self.api_key, base_url=base_url)
            models = client.models.list()
            model_list = [{"id": m.id} for m in models.data]
            return model_list
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', {}).get('message', str(e))
                except:
                    pass
            return {"error": f"获取失败: {error_msg}"}

    def log_frontend_error(self, error_msg: str):
        try:
            log_path = os.path.join(APP_DIR, 'frontend_errors.log')
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                f.write(f"{error_msg}\n\n")
            return "ok"
        except Exception as e:
            print(f"记录前端错误失败: {e}")
            return "error"

    def clear_all_cache(self):
        import shutil
        try:
            if os.path.exists(APP_DIR):
                shutil.rmtree(APP_DIR)
                if self.window:
                    self.window.destroy()
                sys.exit(0)
            return "缓存文件夹不存在"
        except Exception as e:
            return f"清除失败: {str(e)}"

    def has_api_key(self) -> bool:
        return bool(self.api_key)

    def get_last_usage(self):
        if self._last_usage:
            return self._last_usage.copy()
        return {}

    def get_balance(self):
        base_url = self.config.get('api_base', 'https://api.deepseek.com')
        if base_url not in ("https://api.deepseek.com", "https://api.deepseek.com/"):
            return {"error": self.strings.get('balance_deepseek_only', '余额查询仅支持 DeepSeek 官方地址')}
        import requests
        url = "https://api.deepseek.com/user/balance"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def get_models(self):
        if not self.api_key:
            return {"error": self.strings.get('api_key_required_for_models', '请先设置 API 密钥')}
        base_url = self.config.get('api_base', 'https://api.deepseek.com')
        try:
            client = OpenAI(api_key=self.api_key, base_url=base_url)
            models = client.models.list()
            model_list = [{"id": m.id} for m in models.data]
            return model_list
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', {}).get('message', str(e))
                except:
                    pass
            return {"error": f"获取失败: {error_msg}"}

    def __init__(self):
        self.config = load_config()
        self.lang = self.config.get('language', 'zh_Cn')
        self.strings = LANG_STRINGS.get(self.lang, LANG_STRINGS['zh_Cn'])
        self.api_key = get_api_key_from_storage()
        self.model = self.config.get('model', 'deepseek-v4-flash')
        self.think = self.config.get('think', '关')
        self.memory_enabled = self.config.get('memory', False)
        self.web_search_enabled = self.config.get('web_search', False)
        self.messages = []
        self.memory_history = []
        self.memory_summary = ""
        self._last_usage = None
        self.window = None

        self._chunk_queue = []
        self._chunk_index = 0
        self._stream_finished = False
        self._full_reply = ""
        self._full_reasoning = ""

        self._stop_flag = False
        self._stop_event = threading.Event()
        self._manually_stopped = False

        self._load_memory()

    def _load_memory(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.memory_history = data.get('history', [])
                self.memory_summary = data.get('summary', '')
            except Exception:
                pass

    def _save_memory(self):
        data = {
            'history': self.memory_history,
            'summary': self.memory_summary,
        }
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _trim_memory(self):
        if not self.memory_enabled:
            return
        max_rounds = self.config.get('max_rounds', 10)
        mode = self.config.get('memory_mode', 'full')
        total_rounds = len(self.memory_history) // 2
        if total_rounds <= max_rounds:
            return

        if mode == 'full':
            excess = (total_rounds - max_rounds) * 2
            self.memory_history = self.memory_history[excess:]
            self._save_memory()
        else:
            keep_rounds = 2
            keep_count = keep_rounds * 2
            if len(self.memory_history) <= keep_count:
                return
            to_summarize = self.memory_history[:-keep_count]
            recent = self.memory_history[-keep_count:]
            text = "\n".join([f"{m['role']}: {m['content']}" for m in to_summarize])
            def gen_summary():
                try:
                    prompt = f"请用100字以内总结以下对话：\n{text}"
                    messages = [{"role": "user", "content": prompt}]
                    summary = call_deepseek_api_sync(
                        self.api_key,
                        messages,
                        model="deepseek-v4-flash",
                        temperature=0.3,
                        max_tokens=200,
                        base_url=self.config.get('api_base', 'https://api.deepseek.com')
                    )
                    self.memory_summary = summary
                    self.memory_history = recent
                    self._save_memory()
                except Exception as e:
                    print(f"摘要生成失败: {e}")
            threading.Thread(target=gen_summary, daemon=True).start()

    def get_initial_messages(self):
        return self.messages.copy()

    def get_memory_content(self):
        if self.memory_enabled:
            if self.config.get('memory_mode', 'full') == 'summary' and self.memory_summary:
                return f"历史摘要：{self.memory_summary}\n"
            if self.memory_history:
                text = "\n".join([f"{m['role']}: {m['content']}" for m in self.memory_history[-10:]])
                return f"历史对话：\n{text}\n"
        return ""

    def send_message(self, user_text: str, files: List[Dict] = None):
        if not self.api_key:
            return "__ERROR__:未设置API密钥"

        if hasattr(self, '_stream_finished') and not self._stream_finished:
            timeout = 5.0
            start = time.time()
            while not self._stream_finished and time.time() - start < timeout:
                time.sleep(0.01)
            if not self._stream_finished:
                self._stream_finished = True
                self._stop_flag = True
                self._stop_event.set()

        self._chunk_queue = []
        self._chunk_index = 0
        self._stream_finished = False
        self._full_reply = ""
        self._full_reasoning = ""
        self._stop_flag = False
        self._stop_event.clear()
        self._manually_stopped = False

        if files:
            file_contents = "\n\n".join([f"文件 {f['name']}:\n{f['content']}" for f in files])
            full_user_text = f"{user_text}\n\n--- 文件内容 ---\n{file_contents}" if user_text else file_contents
        else:
            full_user_text = user_text

        self.messages.append({"role": "user", "content": full_user_text})
        full_messages = []
        current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        full_messages.append({
            "role": "system",
            "content": f"[SystemPrompt]当前系统时间：{current_time}。"
        })
        memory_text = self.get_memory_content()
        if memory_text:
            full_messages.append({
                "role": "system",
                "content": self.strings['memory_prefix'] + memory_text
            })
        for msg in self.messages:
            if msg["role"] == "user":
                new_content = f"[SystemPrompt]当前系统时间：{current_time}\n{msg['content']}"
                full_messages.append({"role": "user", "content": new_content})
            else:
                full_messages.append(msg)

        custom_model = self.config.get('custom_model', '').strip()
        actual_model = custom_model if custom_model else self.model
        base_url = self.config.get('api_base', 'https://api.deepseek.com')

        kwargs = {
            "temperature": self.config.get('temperature', 1.0),
            "max_tokens": self.config.get('max_tokens', 32767),
            "logprobs": self.config.get('logprobs', False),
            "top_logprobs": self.config.get('top_logprobs', 0),
            "stop_sequences": self.config.get('stop_sequences', ''),
            "user_id": self.config.get('user_id', ''),
            "json_mode": self.config.get('json_mode', False),
        }

        def fill_queue():
            self._stop_event.clear()
            chunk_count = 0
            try:
                for item in call_deepseek_api_stream(
                    api_key=self.api_key,
                    messages=full_messages,
                    model=actual_model,
                    think_level=self.think,
                    enable_web_search=self.web_search_enabled,
                    stop_event=self._stop_event,
                    base_url=base_url,
                    **kwargs
                ):
                    if self._stop_flag:
                        break
                    chunk_count += 1
                    if item.startswith("__ERROR__:"):
                        self._chunk_queue.append(item)
                        break
                    elif item.startswith("__REASONING__:"):
                        reasoning_part = item[len("__REASONING__:"):]
                        self._full_reasoning += reasoning_part
                        self._chunk_queue.append(item)
                    elif item.startswith("__USAGE__:"):
                        usage_str = item[len("__USAGE__:"):]
                        try:
                            parts = usage_str.split(',')
                            self._last_usage = {
                                'prompt_tokens': int(parts[0]),
                                'completion_tokens': int(parts[1])
                            }
                        except Exception:
                            pass
                    else:
                        self._chunk_queue.append(item)
                        self._full_reply += item
            except Exception as e:
                self._chunk_queue.append(f"__ERROR__:{str(e)}")
            finally:
                self._stream_finished = True
                print(f"[DEBUG] fill_queue 完成，共收到 {chunk_count} 个 chunk，队列长度 {len(self._chunk_queue)}")

        threading.Thread(target=fill_queue, daemon=True).start()
        return "ok"

    def stop_generation(self):
        self._stop_event.set()
        self._stop_flag = True
        self._manually_stopped = True

    def get_next_chunk(self):
        if self._chunk_index < len(self._chunk_queue):
            chunk = self._chunk_queue[self._chunk_index]
            self._chunk_index += 1
            return chunk
        elif self._stream_finished:
            if not self._manually_stopped and (self._full_reply or self._full_reasoning):
                assistant_msg = {"role": "assistant", "content": self._full_reply}
                if self._full_reasoning:
                    assistant_msg["reasoning_content"] = self._full_reasoning
                self.messages.append(assistant_msg)
                self.memory_history.append({"role": "user", "content": self.messages[-2]['content']})
                self.memory_history.append({"role": "assistant", "content": self._full_reply})
                self._trim_memory()
                self._save_memory()
            return None
        else:
            return "__WAIT__"

    def get_full_reply(self):
        return self._full_reply

    def get_full_reasoning(self):
        return self._full_reasoning

    def get_config(self):
        return self.config.copy()

    def save_config(self, new_config: Dict):
        old_method = self.config.get('encryption_method')
        self.config.update(new_config)
        new_method = self.config.get('encryption_method')
        save_config(self.config)
        if new_method != old_method and self.api_key:
            self.migrate_encryption(new_method)
        self.lang = self.config.get('language', 'zh_Cn')
        self.strings = LANG_STRINGS.get(self.lang, LANG_STRINGS['zh_Cn'])
        self.model = self.config.get('model', 'deepseek-v4-flash')
        self.think = self.config.get('think', '关')
        self.memory_enabled = self.config.get('memory', False)
        self.web_search_enabled = self.config.get('web_search', False)

    def clear_memory(self):
        if os.path.exists(MEMORY_FILE):
            os.remove(MEMORY_FILE)
            self.memory_history = []
            self.memory_summary = ""
            return True
        return False

    def change_api_key(self, new_key: str):
        base_url = self.config.get('api_base', 'https://api.deepseek.com')
        if validate_api_key(new_key, base_url):
            save_api_key(new_key)
            self.api_key = new_key
            return True
        return False

    def restart_app(self):
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def upload_files(self, files_data: List[Dict]) -> List[Dict]:
        result = []
        for f in files_data:
            try:
                raw = base64.b64decode(f['data'])
                temp_dir = Path(APP_DIR) / 'temp'
                temp_dir.mkdir(exist_ok=True)
                temp_path = temp_dir / f['name']
                with open(temp_path, 'wb') as out:
                    out.write(raw)
                text = extract_text_from_file(str(temp_path))
                try:
                    os.remove(temp_path)
                except:
                    pass
                result.append({
                    'name': f['name'],
                    'size': f['size'],
                    'type': f['type'],
                    'content': text
                })
            except Exception as e:
                result.append({
                    'name': f['name'],
                    'error': str(e)
                })
        return result

HTML_TEMPLATE = r'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NORP API</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; background: #f5f5f5; height: 100vh; overflow: hidden; }
        #app { width: 100%; height: 100vh; display: flex; flex-direction: column; background: #fff; }
        #header { padding: 10px 16px; background: #2c3e50; color: #fff; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; flex-wrap: wrap; gap: 6px; }
        #header h1 { margin: 0; font-size: 17px; }
        #header .btn-group { display: flex; gap: 4px; flex-wrap: wrap; }
        #header button { background: transparent; border: 1px solid rgba(255,255,255,0.4); color: #fff; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 12px; }
        #header button:hover { background: rgba(255,255,255,0.15); }
        #chat { flex: 1; overflow-y: auto; padding: 12px 16px; background: #fafafa; }
        .message { margin-bottom: 10px; }
        .user-msg { text-align: right; }
        .assistant-msg { text-align: left; }
        .user-text { display: inline-block; background: #007aff; color: #fff; padding: 6px 12px; border-radius: 14px; text-align: left; max-width: 85%; word-wrap: break-word; user-select: text; }
        .assistant-text {
            display: block;
            width: fit-content;
            background: #fff;
            color: #000;
            padding: 28px 12px 6px 12px;
            border-radius: 14px;
            border: 1px solid #ddd;
            text-align: left;
            max-width: 85%;
            word-wrap: break-word;
            margin-left: -10px;
            user-select: text;
            position: relative;
        }
        .assistant-text ul,
        .assistant-text ol {
            padding-left: 20px;
            margin: 4px 0;
            list-style-position: inside;
        }
        .assistant-text li {
            margin: 2px 0;
        }
        .assistant-text .btn-group {
            position: absolute;
            top: 4px;
            right: 8px;
            display: flex;
            gap: 4px;
        }
        .assistant-text .btn-group button {
            padding: 2px 10px;
            font-size: 11px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-family: -apple-system, sans-serif;
        }
        .assistant-text .btn-group .test-btn {
            background: #34c759;
            color: #fff;
            display: none;
        }
        .assistant-text .btn-group .test-btn:hover {
            background: #28a745;
        }
        .assistant-text .btn-group .copy-reply-btn {
            background: #e0e0e0;
            color: #333;
            border: 1px solid #ccc;
        }
        .assistant-text .btn-group .copy-reply-btn:hover {
            background: #d0d0d0;
        }
        .file-card { background: #fff; border: 1px solid #ddd; border-radius: 6px; padding: 6px 10px; margin: 3px 0; display: inline-block; text-align: left; min-width: 140px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
        .file-name { font-weight: 500; color: #333; font-size: 13px; }
        .file-meta { font-size: 11px; color: #888; margin-top: 2px; }
        .file-icon { margin-right: 4px; }
        .file-list { display: flex; flex-wrap: wrap; gap: 4px; margin: 3px 0; }
        .reasoning-box { background: #f5f5f5; padding: 6px 10px; border-left: 3px solid #999; font-size: 0.9em; color: #555; margin-bottom: 4px; white-space: pre-wrap; border-radius: 0 4px 4px 0; }
        .reasoning-details { margin-bottom: 4px; background: #f5f5f5; border-radius: 4px; padding: 2px 8px; }
        .reasoning-details summary { cursor: pointer; font-size: 0.9em; color: #555; padding: 4px 0; }
        .reasoning-details summary:hover { color: #333; }
        .reply-box { white-space: pre-wrap; }
        .loading-spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #ddd; border-top: 2px solid #007aff; border-radius: 50%; animation: spin 0.8s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0); } 100% { transform: rotate(360deg); } }
        #input-area { display: flex; flex-wrap: wrap; padding: 6px 10px; border-top: 1px solid #ddd; background: #fff; align-items: center; gap: 4px; flex-shrink: 0; }
        #user-input { flex: 1; min-width: 100px; padding: 6px 12px; border: 1px solid #ddd; border-radius: 16px; outline: none; font-size: 13px; resize: none; height: 80px; }
        #user-input:focus { border-color: #007aff; }
        .btn-action { padding: 4px 12px; border: none; border-radius: 14px; cursor: pointer; font-size: 12px; white-space: nowrap; height: 30px; }
        .btn-send { background: #007aff; color: #fff; }
        .btn-send:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-stop { background: #dc3545; color: #fff; display: none; }
        .btn-upload { background: #6c757d; color: #fff; font-size: 14px; padding: 0 10px; }
        #file-badges { display: flex; flex-wrap: wrap; gap: 3px; align-items: center; max-width: 160px; overflow: hidden; }
        .file-badge { background: #e8e8e8; padding: 1px 6px; border-radius: 8px; font-size: 10px; color: #333; display: inline-flex; align-items: center; gap: 2px; white-space: nowrap; }
        .file-badge .remove { cursor: pointer; color: #999; font-weight: bold; margin-left: 2px; }
        .file-badge .remove:hover { color: #dc3545; }
        #status-bar { font-size: 11px; color: #888; padding: 2px 12px; background: #f0f0f0; border-top: 1px solid #eee; flex-shrink: 0; display: flex; justify-content: space-between; align-items: center; }
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.4); }
        .modal-content { background-color: #fefefe; margin: 3% auto; padding: 16px; border: 1px solid #888; width: 90%; max-width: 440px; border-radius: 8px; max-height: 85vh; overflow-y: auto; }
        .modal-content label { display: block; margin: 6px 0 3px; font-weight: 500; font-size: 12px; }
        .modal-content select, .modal-content input[type="text"], .modal-content input[type="number"] { width: 100%; padding: 4px 8px; margin-bottom: 4px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px; }
        .modal-content input[type="checkbox"] { margin-right: 4px; }
        .modal-content input[type="range"] { width: 100%; }
        .modal-content .btn-group { display: flex; gap: 6px; margin-top: 10px; flex-wrap: wrap; }
        .modal-content .btn-primary { background: #007aff; color: #fff; border: none; padding: 5px 14px; border-radius: 4px; cursor: pointer; }
        .modal-content .btn-danger { background: #dc3545; color: #fff; border: none; padding: 5px 14px; border-radius: 4px; cursor: pointer; }
        .modal-content .btn-secondary { background: #6c757d; color: #fff; border: none; padding: 5px 14px; border-radius: 4px; cursor: pointer; }
        .advanced-section { display: none; margin-top: 6px; border-top: 1px solid #ddd; padding-top: 6px; }
        .advanced-section.show { display: block; }
        .disabled-text { color: #999; font-size: 0.8em; margin-left: 4px; }
        .code-block-wrapper { background: #f5f5f5; border: 1px solid #ddd; border-radius: 4px; margin: 4px 0; position: relative; }
        .code-header { background: #e8e8e8; padding: 0 8px; display: flex; justify-content: space-between; align-items: center; border-radius: 4px 4px 0 0; height: 26px; line-height: 26px; position: sticky; top: 0; z-index: 10; border-bottom: 1px solid #ddd; }
        .code-language { font-weight: 600; font-size: 11px; color: #555; line-height: 26px; }
        .code-header div { display: flex; align-items: center; gap: 0; height: 26px; }
        .code-header button { padding: 1px 8px; font-size: 10px; border: none; border-radius: 3px; cursor: pointer; height: 20px; line-height: 20px; margin: 0 2px; }
        .code-block-wrapper pre {
            margin: 0;
            padding: 4px 8px;
            overflow-x: auto;
            background: #fafafa;
            border-radius: 0 0 4px 4px;
            font-size: 12px;
            line-height: 1.4;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .code-block-wrapper code {
            font-family: monospace;
            font-size: 12px;
            line-height: 1.4;
            display: block;
        }
        .math-inline-wrapper { position: relative; display: inline-block; }
        .math-copy-btn {
            position: absolute;
            top: 4px;
            right: 4px;
            padding: 2px 8px;
            font-size: 10px;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            background: #e0e0e0;
            color: #333;
            opacity: 0;                      
            transition: opacity 0.2s;
        }
        .math-display-wrapper:hover .math-copy-btn,
        .math-inline-wrapper:hover .math-copy-btn {
            opacity: 1;                      
        }
        #loading-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.92); display: flex; justify-content: center; align-items: center; z-index: 9999; flex-direction: column; gap: 10px; }
        #loading-overlay .spinner { width: 32px; height: 32px; border: 3px solid #ddd; border-top: 3px solid #007aff; border-radius: 50%; animation: spin 0.8s linear infinite; }
        #loading-overlay .text { font-size: 15px; color: #333; }
        #toast-container { position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%); z-index: 2000; }
        .toast { background: #333; color: #fff; padding: 4px 14px; border-radius: 14px; font-size: 12px; opacity: 0; transition: opacity 0.3s; margin-bottom: 4px; }
        .toast.show { opacity: 1; }
        @media (max-width: 600px) {
            #header { padding: 6px 10px; }
            #header h1 { font-size: 15px; }
            #chat { padding: 8px 10px; }
            .user-text, .assistant-text { max-width: 90%; }
            #input-area { padding: 4px 6px; gap: 3px; }
            #user-input { font-size: 12px; padding: 4px 8px; height: 28px; }
            .btn-action { font-size: 11px; padding: 3px 8px; height: 26px; }
            #file-badges { max-width: 100px; }
            .modal-content { padding: 12px; }
        }
        .markdown-table {
            border-collapse: collapse;
            width: 100%;
            margin: 8px 0;
            font-size: 13px;
        }
        .markdown-table th,
        .markdown-table td {
            border: 1px solid #ccc;
            padding: 6px 10px;
            text-align: left;
        }
        .markdown-table th {
            background-color: #f2f2f2;
            font-weight: 600;
        }
        .markdown-table tr:nth-child(even) {
            background-color: #fafafa;
        }
        #chat {
            flex: 1;
            overflow-y: auto;
            padding: 12px 16px;
            background: #fafafa;
            position: relative;
        }
        #external-viewer {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: #fff;
            z-index: 9999;
            display: none;
            flex-direction: column;
        }
        #external-viewer iframe {
            width: 100%;
            height: 100%;
            border: none;
        }
        #external-viewer .back-btn {
            position: fixed;
            top: 16px;
            left: 16px;
            padding: 8px 20px;
            background: rgba(0, 0, 0, 0.75);
            color: #fff;
            border: none;
            border-radius: 24px;
            cursor: pointer;
            font-size: 16px;
            z-index: 10000;
            backdrop-filter: blur(6px);
            font-family: -apple-system, sans-serif;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        #external-viewer .back-btn:hover {
            background: rgba(0, 0, 0, 0.95);
        }
    </style>
</head>
<body>
    <div id="loading-overlay">
        <div class="spinner"></div>
        <div class="text" data-i18n="loading_text">加载中，请稍候...</div>
    </div>

    <div id="app" style="display:none;">
        <div id="header">
            <h1 id="title">NORP API</h1>
            <div class="btn-group">
                <button id="about-btn" data-i18n="about">关于</button>
                <button id="balance-btn" data-i18n="余额">余额</button>
                <button id="refresh-text-btn" data-i18n="refresh_text">刷新</button>
                <button id="reset-page-btn" data-i18n="reset_page">重置</button>
                <button id="settings-btn" data-i18n="settings">设置</button>
                <button id="key-btn" data-i18n="change_key">密钥</button>
            </div>
        </div>

        <div id="chat"></div>

        <div id="external-viewer">
            <button class="back-btn" id="external-back-btn">← 返回</button>
            <iframe id="external-iframe" sandbox="allow-scripts allow-same-origin allow-forms allow-popups"></iframe>
        </div>

        <div id="input-area">
            <textarea id="user-input" rows="1" placeholder="输入消息..." disabled></textarea>
            <button class="btn-action btn-upload" id="upload-btn">文件</button>
            <input type="file" id="file-input" style="display:none" multiple>
            <div id="file-badges"></div>
            <button class="btn-action btn-send" id="send-btn" disabled>发送</button>
            <button class="btn-action btn-stop" id="stop-btn" style="display:none;">停止</button>
        </div>

        <div id="status-bar">
            <span id="status-text">就绪</span>
            <span id="file-count"></span>
        </div>
    </div>

    <div id="settings-modal" class="modal">
        <div class="modal-content">
            <h2>设置</h2>
            <label data-i18n="language_label">语言</label>
            <select id="lang-select">
                <option value="zh_Cn">简体中文</option>
                //<option value="zh_Tw">繁體中文</option>
                <option value="en">English</option>
                //<option value="ja">日本語</option>
                //<option value="ru">Русский</option>
            </select>
            <label data-i18n="model_select">模型</label>
            <select id="model-select">
                <!-- 由 JavaScript 动态填充 -->
            </select>
            <label data-i18n="think_label">思考强度</label>
            <select id="think-select">
                <option value="关">关</option>
                <option value="低">低</option>
                <option value="中">中</option>
                <option value="高">最高（深度推理）</option>
            </select>
            <label><input type="checkbox" id="memory-check"> <span data-i18n="memory_label">开启记忆 (Beta)</span></label>
            <label><input type="checkbox" id="web-search-check"> <span data-i18n="web_search_label">联网搜索</span></label>
            <label><input type="checkbox" id="advanced-toggle"> <span data-i18n="advanced_enabled_label">启用高级设置</span></label>
            <div id="advanced-section" class="advanced-section">
                <label data-i18n="temperature_label">温度</label>
                <input type="range" id="temperature-slider" min="0" max="20" step="1" value="10">
                <span id="temperature-value">1.0</span>
                <label data-i18n="max_tokens_label">最大输出长度</label>
                <input type="number" id="max-tokens-input" min="1" max="65536" step="1" value="32767">
                <label><input type="checkbox" id="logprobs-check"> <span data-i18n="logprobs_label">返回对数概率</span></label>
                <label data-i18n="top_logprobs_label">Top对数概率个数</label>
                <input type="number" id="top-logprobs-input" min="0" max="20" value="0" disabled>
                <label><input type="checkbox" id="show-reasoning-check" checked> <span data-i18n="show_reasoning_label">显示思考过程</span></label>
                <label><input type="checkbox" id="json-mode-check"> <span data-i18n="json_mode_label">JSON输出模式</span></label>
                <label data-i18n="stop_sequences_label">停止序列 (逗号分隔)</label>
                <input type="text" id="stop-sequences-input" placeholder="例如: stop1, stop2">
                <label data-i18n="user_id_label">用户标识</label>
                <input type="text" id="user-id-input" placeholder="可选">
                <hr>
                <label data-i18n="custom_model_label">自定义模型名称</label>
                <input type="text" id="custom-model-input" placeholder="例如: deepseek-chat">
                <label data-i18n="encryption_method_label">密钥存储方式</label>
                <select id="encryption-method-select">
                    <option value="win32crypt">DPAPI（默认，兼容）</option>
                    <option value="keyring">Windows 凭据管理器（更安全） (Keyring)</option>
                </select>
                <label data-i18n="api_base_label">API 地址</label>
                <div style="display:flex; gap:6px; align-items:center;">
                    <input type="text" id="api-base-input" placeholder="https://api.deepseek.com" value="https://api.deepseek.com" style="flex:1; padding:4px 8px; border:1px solid #ddd; border-radius:4px;">
                    <button class="btn-primary" id="apply-api-btn" style="padding:4px 12px; font-size:12px; border:none; border-radius:4px; cursor:pointer; background:#007aff; color:#fff; white-space:nowrap;">应用</button>
                </div>
                <div style="display:flex; gap:6px; align-items:center; margin-bottom:6px;">
                    <button class="btn-secondary" id="fetch-models-btn" style="padding:4px 12px; font-size:12px; border:none; border-radius:4px; cursor:pointer; background:#6c757d; color:#fff;">获取模型列表</button>
                    <span id="fetch-status" style="font-size:12px; color:#888;"></span>
                </div>
            </div>
            <hr>
            <h3>记忆设置</h3>
            <label data-i18n="memory_mode_label">记忆模式</label>
            <select id="memory-mode-select">
                <option value="full">完整</option>
                <option value="summary">精简</option>
            </select>
            <label data-i18n="max_rounds_label">记忆轮数</label>
            <input type="number" id="max-rounds-input" min="1" max="50" value="10">
            <button class="btn-danger" id="clear-memory-btn" data-i18n="clear_memory">清除记忆</button>
            <hr>
            <div style="display:flex; gap:8px; flex-wrap:wrap; margin:10px 0;">
                <button class="btn-danger" id="clear-cache-btn" style="padding:6px 16px; border:none; border-radius:4px; cursor:pointer; background:#dc3545; color:#fff;">清除所有缓存</button>
            </div>
            <div class="btn-group">
                <button class="btn-primary" id="settings-save" data-i18n="confirm">确定</button>
                <button class="btn-secondary" id="settings-cancel" data-i18n="cancel">取消</button>
            </div>
        </div>
    </div>

    <div id="toast-container"></div>
    <div id="about-modal" class="modal" style="display:none;">
        <div class="modal-content">
            <h2>关于本程序</h2>
            <p><strong>作者：</strong>xingluosama</p>
            <p><strong>所属：</strong>NORP Studio</p>
            <p><strong>版本：</strong>Beta 1.0.0</p>
            <p style="margin-top:12px; color:#888; font-size:12px;">基于 OpenAI SDK 构建</p>
            <div style="margin-top:15px;">
                <button class="btn-primary" id="about-close-btn" data-i18n="confirm">确定</button>
            </div>
        </div>
    </div>

    <script>
        let messages = [];
        let isWaiting = false;
        let isStreaming = false;
        let currentAssistantEl = null;
        let pendingReasoning = '';
        let pendingReply = '';
        let reasoningTimer = null;
        let replyTimer = null;
        let pollingTimer = null;
        let renderTimer = null;
        let fullReply = '';
        let fullReasoning = '';
        let currentLang = 'zh_Cn';
        let i18n = {};
        let isStopped = false;
        let selectedFiles = [];
        let waitCount = 0;
        const MAX_WAIT = 2400;
        let userScrolled = false;

        const chatDiv = document.getElementById('chat');
        const userInput = document.getElementById('user-input');
        const sendBtn = document.getElementById('send-btn');
        const stopBtn = document.getElementById('stop-btn');
        const uploadBtn = document.getElementById('upload-btn');
        const fileInput = document.getElementById('file-input');
        const fileBadges = document.getElementById('file-badges');
        const fileCount = document.getElementById('file-count');
        const statusText = document.getElementById('status-text');
        const settingsModal = document.getElementById('settings-modal');
        const settingsBtn = document.getElementById('settings-btn');
        const keyBtn = document.getElementById('key-btn');
        const toastContainer = document.getElementById('toast-container');
        const advancedToggle = document.getElementById('advanced-toggle');
        const advancedSection = document.getElementById('advanced-section');
        const loadingOverlay = document.getElementById('loading-overlay');
        const appContainer = document.getElementById('app');


        chatDiv.addEventListener('scroll', function() {
            const isAtBottom = chatDiv.scrollHeight - chatDiv.scrollTop - chatDiv.clientHeight < 10;
            userScrolled = !isAtBottom;
        });

        function scrollToBottomIfNeeded() {
            if (!userScrolled) {
                chatDiv.scrollTop = chatDiv.scrollHeight;
            }
        }


        chatDiv.addEventListener('click', function(e) {
            // 1. 处理代码块测试按钮
            const testTarget = e.target.closest('.test-html-btn');
            if (testTarget) {
                e.preventDefault();
                e.stopPropagation();
                const code = testTarget.dataset.code || '';
                if (code) {
                    openHTMLContent(decodeURIComponent(code));
                }
                return;
            }


            const mathCopyBtn = e.target.closest('.math-copy-btn');
            if (mathCopyBtn) {
                e.preventDefault();
                e.stopPropagation();
                const encodedLatex = mathCopyBtn.dataset.latex || '';
                if (encodedLatex) {
                    const latex = decodeURIComponent(encodedLatex);
                    if (navigator.clipboard && navigator.clipboard.writeText) {
                        navigator.clipboard.writeText(latex).then(() => showToast(i18n.copy_success || '已复制')).catch(() => fallbackCopy(latex));
                    } else {
                        fallbackCopy(latex);
                    }
                }
                return;
            }


            const target = e.target.closest('a');
            if (target && target.href) {
                if (target.href.startsWith('http://') || target.href.startsWith('https://')) {
                    e.preventDefault();
                    e.stopPropagation();
                    openExternal(target.href);
                }
                return;
            }
        });


        const balanceBtn = document.getElementById('balance-btn');
        if (balanceBtn) {
            balanceBtn.addEventListener('click', async () => {
                try {
                    const data = await pywebview.api.get_balance();
                    if (data.error) {
                        showToast('查询余额失败: ' + data.error);
                    } else if (data.balance_infos && data.balance_infos.length > 0) {
                        const info = data.balance_infos[0];
                        alert(`余额: ¥${info.total_balance}\n(赠送: ¥${info.granted_balance}, 充值: ¥${info.topped_up_balance})`);
                    } else {
                        showToast('余额数据异常');
                    }
                } catch(e) {
                    showToast('查询失败: ' + e.message);
                }
            });
        }


        function showToast(msg, duration) {
            duration = duration || 2000;
            const div = document.createElement('div');
            div.className = 'toast';
            div.textContent = msg;
            toastContainer.appendChild(div);
            setTimeout(() => div.classList.add('show'), 10);
            setTimeout(() => {
                div.classList.remove('show');
                setTimeout(() => div.remove(), 300);
            }, duration);
        }

        function setStatus(msg) {
            statusText.textContent = msg;
        }

        function formatSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }

        function getFileIcon(ext) {
            const icons = {'py':'🐍','js':'📜','html':'🌐','css':'🎨','json':'📋','csv':'📊','txt':'📄','md':'📝','pdf':'📕','docx':'📘','xlsx':'📗'};
            return icons[ext] || '📎';
        }


        function safeKatex(latex, displayMode) {
            try {
                return katex.renderToString(latex, { displayMode: displayMode, throwOnError: false, trust: true });
            } catch (err) {
                const escaped = latex.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                return '<code style="color:#dc3545;background:#fff5f5;padding:2px 6px;border-radius:3px;font-size:0.85em;" title="KaTeX render error: ' + err.message.replace(/"/g, '&quot;') + '">' + escaped + '</code>';
            }
        }

        function renderContent(text) {
            if (!text) return '';
            if (typeof marked === 'undefined') {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }

            try {
                let processed = text.replace(/\u200B/g, '').replace(/\uFEFF/g, '');


                const lines = processed.split('\n');
                const newLines = [];
                const fencedBlocks = [];
                let inCode = false;
                let lang = '';
                let content = [];

                for (let i = 0; i < lines.length; i++) {
                    const line = lines[i];
                  
                    const startMatch = line.match(/^```(\s*)(\w*)/);
                    const endMatch = line.match(/^```\s*$/);

                    if (!inCode) {
                     
                        if (startMatch) {
                            inCode = true;
                            lang = startMatch[2] || '';
                            content = [];
                            const idx = fencedBlocks.length;
                            fencedBlocks.push({ lang: lang, code: '', unclosed: false });
                            newLines.push(`§§FENCED_${idx}§§`);
                        } else {
                            newLines.push(line);
                        }
                    } else {
                        
                        if (endMatch) {
                            const code = content.join('\n');
                            const lastBlock = fencedBlocks[fencedBlocks.length - 1];
                            lastBlock.code = code;
                            lastBlock.unclosed = false;
                            inCode = false;
                            lang = '';
                            content = [];
                        } else {
                            content.push(line);
                        }
                    }
                }

                if (inCode) {
                    const code = content.join('\n');
                    const lastBlock = fencedBlocks[fencedBlocks.length - 1];
                    lastBlock.code = code;
                    lastBlock.unclosed = true;
                }

                processed = newLines.join('\n');


                const inlineCodes = [];
                processed = processed.replace(/(`+)([^`]+?)\1/g, (match, ticks, code) => {
                    inlineCodes.push(code);
                    return `§§INLINE_${inlineCodes.length - 1}§§`;
                });

                const displayMaths = [];
                const inlineMaths = [];

                processed = processed.replace(/\$\$([\s\S]*?)\$\$/g, (match, math) => {
                    displayMaths.push(math.trim());
                    return `§§MATH_DISPLAY_${displayMaths.length - 1}§§`;
                });
                processed = processed.replace(/\\\[([\s\S]*?)\\\]/g, (match, math) => {
                    displayMaths.push(math.trim());
                    return `§§MATH_DISPLAY_${displayMaths.length - 1}§§`;
                });
                processed = processed.replace(/\\\((.*?)\\\)/g, (match, math) => {
                    inlineMaths.push(math.trim());
                    return `§§MATH_INLINE_${inlineMaths.length - 1}§§`;
                });
                processed = processed.replace(/(?<=^|[^\w\$§])\$(?!\$)([^$\n]+?)\$(?![a-zA-Z0-9])/g, (match, math) => {
                    inlineMaths.push(math.trim());
                    return `§§MATH_INLINE_${inlineMaths.length - 1}§§`;
                });

 
                let html = marked.parse(processed);


                html = html.replace(/§§INLINE_(\d+)§§/g, (match, idx) => {
                    const code = inlineCodes[parseInt(idx)] || '';
                    const escaped = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                    return `<code>${escaped}</code>`;
                });

                
                html = html.replace(/§§FENCED_(\d+)§§/g, (match, idx) => {
                    const block = fencedBlocks[parseInt(idx)] || { lang: '', code: '', unclosed: false };
                    let rawCode = block.code.trim();
                    rawCode = rawCode.replace(/\n{3,}/g, '\n\n');
                    const displayCode = rawCode.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                    const encodedRaw = encodeURIComponent(rawCode);
                    const langClass = block.lang ? ` class="language-${block.lang}"` : '';
                    let testBtnHtml = '';
                    const langLower = block.lang.toLowerCase();
                    if (langLower === 'html' || /<!DOCTYPE|<html|<body/i.test(rawCode)) {
                        testBtnHtml = `<button class="test-html-btn" data-code="${encodedRaw}">测试</button>`;
                    }
                    const unclosedLabel = block.unclosed ? ' <span style="font-weight:normal;color:#999;font-size:10px;">(未闭合)</span>' : '';
                    return `<div class="code-block-wrapper"><div class="code-header"><span class="code-language">${block.lang || 'text'}${unclosedLabel}</span><div>${testBtnHtml}<button class="copy-btn" data-code="${encodedRaw}">复制</button></div></div><pre><code${langClass}>${displayCode}</code></pre></div>`;
                });

                
                if (typeof katex !== 'undefined') {
                    html = html.replace(/<p>\s*§§MATH_DISPLAY_(\d+)§§\s*<\/p>/g, (match, idx) => {
                        const latex = displayMaths[parseInt(idx)] || '';
                        const rendered = safeKatex(latex, true);
                        const encodedLatex = encodeURIComponent(latex);
                        return `<div class="math-display-wrapper"><div class="math-display" style="position:relative;display:inline-block;" data-latex="${encodedLatex}">${rendered}<button class="math-copy-btn" data-latex="${encodedLatex}" style="opacity:0.5;top:-15px;right:-10px;">复制该公式</button></div></div>`;
                    });
                    html = html.replace(/§§MATH_DISPLAY_(\d+)§§/g, (match, idx) => {
                        const latex = displayMaths[parseInt(idx)] || '';
                        const rendered = safeKatex(latex, true);
                        const encodedLatex = encodeURIComponent(latex);
                        return `<div class="math-display-wrapper"><div class="math-display" style="position:relative;display:inline-block;" data-latex="${encodedLatex}">${rendered}<button class="math-copy-btn" data-latex="${encodedLatex}" style="opacity:0.5;top:-15px;right:-10px;">复制该公式</button></div></div>`;
                    });
                    html = html.replace(/§§MATH_INLINE_(\d+)§§/g, (match, idx) => {
                        const latex = inlineMaths[parseInt(idx)] || '';
                        const rendered = safeKatex(latex, false);
                        const encodedLatex = encodeURIComponent(latex);
                        return `<span class="math-inline-wrapper" style="position:relative;display:inline-block;"><span class="math-inline" data-latex="${encodedLatex}">${rendered}</span><button class="math-copy-btn" data-latex="${encodedLatex}" style="top:-12px;right:-18px;">复制该公式</button></span>`;
                    });
                } else {
                    html = html.replace(/§§MATH_DISPLAY_(\d+)§§/g, (m, i) => '$$' + (displayMaths[parseInt(i)] || '') + '$$');
                    html = html.replace(/§§MATH_INLINE_(\d+)§§/g, (m, i) => '\\(' + (inlineMaths[parseInt(i)] || '') + '\\)');
                }

                
                html = html.replace(/<table>/g, '<table class="markdown-table">');
                return html;
            } catch (e) {
                try { pywebview.api.log_frontend_error('[renderContent] ' + e.message); } catch (_) {}
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
        }

        function loadI18n(lang) {
            const strings = {
                'zh_Cn': {
                    title: 'NORP API', send: '发送', stop: '停止', settings: '设置',
                    change_key: '更换密钥', clear_memory: '清除记忆', file_upload: '上传',
                    language_label: '语言', model_select: '模型', think_label: '思考强度',
                    memory_label: '开启记忆 (Beta)', web_search_label: '联网搜索',
                    temperature_label: '温度', max_tokens_label: '最大输出长度',
                    logprobs_label: '返回对数概率', top_logprobs_label: 'Top对数概率个数',
                    show_reasoning_label: '显示思考过程', json_mode_label: 'JSON输出模式',
                    stop_sequences_label: '停止序列 (逗号分隔)', user_id_label: '用户标识',
                    memory_mode_label: '记忆模式', max_rounds_label: '记忆轮数',
                    memory_mode_full: '完整', memory_mode_summary: '精简 (摘要)',
                    confirm: '确定', cancel: '取消', settings_saved: '设置已保存',
                    file_too_large: '文件过大 (最大10MB)', file_unsupported: '不支持的文件格式',
                    advanced_enabled_label: '启用高级设置',
                    input_placeholder: '输入消息... (Enter发送, Ctrl+Enter换行)',
                    generation_stopped: '已停止生成', load_memory: '已加载记忆',
                    no_reply: '(助手没有回复)', reasoning_title: '思考过程',
                    stopped: '已停止', loading_text: '加载中，请稍候...',
                    refresh_text: '刷新', reset_page: '重置',
                    drop_hint: '拖入文件或点击选择',
                    send_files: '已发送 ({count} 个文件)',
                    file_too_large_msg: '文件过大: {name} (最大10MB)',
                    unsupported_format: '不支持: {name} (.{ext})',
                    read_error: '读取失败: {name} - {error}',
                    added_files: '已添加 {count} 个文件', file_removed: '已移除文件',
                    no_file_or_text: '请选择文件或输入文本', copy_success: '已复制',
                    reset_confirm: '确定重置页面吗？', reset_done: '页面已重置',
                    config_loaded: '配置已加载', config_saved: '设置已保存',
                    language_changed_restart: '语言已更改，需要重启程序生效。是否立即重启？',
                    api_base_label: 'API 地址',
                    api_base_placeholder: '例如: https://api.deepseek.com',
                    fetch_models_btn: '获取模型列表',
                    fetch_models_success: '已获取 {count} 个模型',
                    fetch_models_error: '获取模型列表失败: {error}',
                    api_key_required_for_models: '请先设置有效的 API 密钥',
                    balance_deepseek_only: '余额查询仅支持 DeepSeek 官方地址',
                    custom_model_label: '自定义模型名称（留空则使用下拉选择）',
                },
                'en': {
                    title: 'NORP API ', send: 'Send', stop: 'Stop', settings: 'Settings',
                    change_key: 'Change Key', clear_memory: 'Clear Memory', file_upload: 'Upload',
                    language_label: 'Language', model_select: 'Model', think_label: 'Reasoning',
                    memory_label: 'Enable Memory (Beta)', web_search_label: 'Web Search',
                    temperature_label: 'Temperature', max_tokens_label: 'Max Tokens',
                    logprobs_label: 'Logprobs', top_logprobs_label: 'Top Logprobs',
                    show_reasoning_label: 'Show Reasoning', json_mode_label: 'JSON Mode',
                    stop_sequences_label: 'Stop Sequences (comma)',
                    user_id_label: 'User ID', memory_mode_label: 'Memory Mode',
                    max_rounds_label: 'Max Rounds', memory_mode_full: 'Full',
                    memory_mode_summary: 'Summary', confirm: 'Confirm', cancel: 'Cancel',
                    settings_saved: 'Settings saved', file_too_large: 'File too large (max 10MB)',
                    file_unsupported: 'Unsupported format', advanced_enabled_label: 'Enable Advanced',
                    input_placeholder: 'Type message... (Enter to send, Ctrl+Enter new line)',
                    generation_stopped: 'Generation stopped', load_memory: 'Memory loaded',
                    no_reply: '(No reply)', reasoning_title: 'Reasoning', stopped: 'Stopped',
                    loading_text: 'Loading...', refresh_text: 'Refresh', reset_page: 'Reset',
                    drop_hint: 'Drop files or click to select',
                    send_files: 'Sent ({count} files)',
                    file_too_large_msg: 'File too large: {name} (max 10MB)',
                    unsupported_format: 'Unsupported: {name} (.{ext})',
                    read_error: 'Read error: {name} - {error}',
                    added_files: 'Added {count} files', file_removed: 'File removed',
                    no_file_or_text: 'Select a file or enter text', copy_success: 'Copied',
                    reset_confirm: 'Reset the page?', reset_done: 'Page reset',
                    config_loaded: 'Config loaded', config_saved: 'Settings saved',
                    language_changed_restart: 'Language changed. Restart to apply?',
                    api_base_label: 'API Base URL',
                    api_base_placeholder: 'e.g. https://api.deepseek.com',
                    fetch_models_btn: 'Fetch Models',
                    fetch_models_success: 'Fetched {count} models',
                    fetch_models_error: 'Failed to fetch models: {error}',
                    api_key_required_for_models: 'Please set a valid API key first',
                    balance_deepseek_only: 'Balance query only supports DeepSeek official endpoint',
                    custom_model_label: 'Custom model name (leave empty to use dropdown)',
                }
            };
            i18n = strings[lang] || strings['zh_Cn'];
            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                if (i18n[key]) el.textContent = i18n[key];
            });
            document.title = i18n.title || 'NORP API';
            document.querySelector('#title').textContent = i18n.title || 'NORP API';
            userInput.placeholder = i18n.input_placeholder || '输入消息...';
            document.querySelector('#api-base-input')?.setAttribute('placeholder', i18n.api_base_placeholder || 'https://api.deepseek.com');
        }


        function addUserMessage(text, files) {
            let html = '<div class="user-msg"><div class="user-text" style="white-space:pre-wrap;">';
            if (files && files.length > 0) {
                html += '<div class="file-list">';
                files.forEach(f => {
                    const icon = getFileIcon(f.type);
                    html += `<div class="file-card"><div class="file-name"><span class="file-icon">${icon}</span>${f.name}</div><div class="file-meta">${formatSize(f.size)} <span style="background:#e8e8e8;padding:0 4px;border-radius:2px;font-size:10px;">.${f.type}</span></div></div>`;
                });
                html += '</div>';
            }
            if (text) {
                const escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                html += `<div style="margin-top:3px;white-space:pre-wrap;">${escaped}</div>`;
            }
            html += '</div></div>';
            const div = document.createElement('div');
            div.className = 'message';
            div.innerHTML = html;

            const userTextDiv = div.querySelector('.user-text > div:last-child');
            if (userTextDiv) userTextDiv.dataset.raw = text;
            chatDiv.appendChild(div);
            scrollToBottomIfNeeded();
        }

        function createAssistantMessage() {
            const div = document.createElement('div');
            div.className = 'message assistant-msg';
            const details = document.createElement('details');
            details.className = 'reasoning-details';
            details.open = true;
            const summary = document.createElement('summary');
            summary.textContent = i18n.reasoning_title || '思考过程';
            details.appendChild(summary);
            const reasoningDiv = document.createElement('div');
            reasoningDiv.className = 'reasoning-box';
            details.appendChild(reasoningDiv);
            div.appendChild(details);

            const replyDiv = document.createElement('div');
            replyDiv.className = 'reply-box assistant-text';
            div.appendChild(replyDiv);

            const copyBtn = document.createElement('button');
            copyBtn.className = 'copy-reply-btn';
            copyBtn.textContent = '复制';
            copyBtn.style.cssText = 'margin-top:4px;padding:2px 10px;font-size:11px;background:#e0e0e0;color:#333;border:1px solid #ccc;border-radius:4px;cursor:pointer;display:none;';
            copyBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                const mathEls = replyDiv.querySelectorAll('.math-inline, .math-display');
                let fullText = '';
                for (const node of replyDiv.childNodes) {
                    if (node.nodeType === Node.TEXT_NODE) {
                        fullText += node.textContent;
                    } else if (node.classList && (node.classList.contains('math-inline') || node.classList.contains('math-display'))) {
                        const latex = decodeURIComponent(node.dataset.latex || '');
                        if (node.classList.contains('math-inline')) {
                            fullText += `\\(${latex}\\)`;
                        } else {
                            fullText += `\\[${latex}\\]`;
                        }
                    } else {
                        fullText += node.textContent || '';
                    }
                }
                if (!fullText.trim()) {
                    fullText = replyDiv.textContent || '';
                }
                if (fullText) {
                    (navigator.clipboard && navigator.clipboard.writeText) ?
                        navigator.clipboard.writeText(fullText).then(() => showToast(i18n.copy_success || '已复制')).catch(() => fallbackCopy(fullText)) :
                        fallbackCopy(fullText);
                }
            });
            div.appendChild(copyBtn);

            div._reasoningDetails = details;
            div._reasoningEl = reasoningDiv;
            div._replyEl = replyDiv;
            div._copyBtn = copyBtn;
            return div;
        }

        function addLoadingMessage() {
            const div = document.createElement('div');
            div.className = 'message assistant-msg';
            div.id = 'loading-message';
            div.innerHTML = `<div class="assistant-text"><span class="loading-spinner"></span></div>`;
            chatDiv.appendChild(div);
            scrollToBottomIfNeeded();
        }

        function removeLoadingMessage() {
            const el = document.getElementById('loading-message');
            if (el) el.remove();
        }

        function showError(msg) {
            const div = document.createElement('div');
            div.className = 'message assistant-msg';
            div.innerHTML = `<div class="assistant-text" style="color:red;">错误: ${msg}</div>`;
            chatDiv.appendChild(div);
            scrollToBottomIfNeeded();
        }

        function setInputEnabled(enabled) {
            sendBtn.disabled = !enabled;
            if (enabled) {
                stopBtn.style.display = 'none';
                userInput.focus();
            } else {
                stopBtn.style.display = 'inline-block';
            }
        }


        function typeReasoningChar() {
            if (pendingReasoning.length === 0) { clearInterval(reasoningTimer); reasoningTimer = null; return; }
            const ch = pendingReasoning[0];
            pendingReasoning = pendingReasoning.slice(1);
            const el = currentAssistantEl._reasoningEl;
            if (!el) return;
            if (!el.dataset.raw) el.dataset.raw = '';
            el.dataset.raw += ch;
            el.textContent = el.dataset.raw;
            scrollToBottomIfNeeded();
        }

        function typeReplyChar() {
            if (pendingReply.length === 0) { clearInterval(replyTimer); replyTimer = null; return; }
            const ch = pendingReply[0];
            pendingReply = pendingReply.slice(1);
            const el = currentAssistantEl._replyEl;
            if (!el) return;
            if (!el.dataset.raw) el.dataset.raw = '';
            el.dataset.raw += ch;
            el.innerHTML = renderContent(el.dataset.raw);
            scrollToBottomIfNeeded();
        }

        async function finishStream() {
            if (renderTimer) { clearTimeout(renderTimer); renderTimer = null; }
            if (reasoningTimer) clearInterval(reasoningTimer);
            if (replyTimer) clearInterval(replyTimer);
            if (pollingTimer) clearInterval(pollingTimer);

            let reasoning = '';
            try { reasoning = await pywebview.api.get_full_reasoning(); } catch(e) {}

            if (currentAssistantEl) {
                const rEl = currentAssistantEl._reasoningEl;
                const pEl = currentAssistantEl._replyEl;
                const finalReply = fullReply || (pEl ? pEl.dataset.raw : '') || '';
                const finalReasoning = reasoning || (rEl ? rEl.dataset.raw : '') || '';

                if (rEl) {
                    if (finalReasoning.trim()) {
                        rEl.textContent = finalReasoning;
                    } else {
                        rEl.textContent = '';
                        if (currentAssistantEl._reasoningDetails) {
                            currentAssistantEl._reasoningDetails.style.display = 'none';
                        }
                    }
                }

                let displayContent = finalReply;
                if (!displayContent.trim() && finalReasoning.trim()) {
                    displayContent = finalReasoning;
                }

                if (pEl) {
                    if (displayContent.trim()) {
                        pEl.innerHTML = renderContent(displayContent);
                    } else {
                        pEl.textContent = i18n.no_reply || '(无回复)';
                    }
                }

                const copyBtn = currentAssistantEl._copyBtn;
                if (copyBtn) copyBtn.style.display = 'inline-block';

                messages.push({role: 'assistant', content: finalReply});
                currentAssistantEl = null;
            }

            isStreaming = false;
            isWaiting = false;
            setInputEnabled(true);
            removeLoadingMessage();

            if (isStopped) {
                showToast(i18n.generation_stopped || '已停止生成');
                isStopped = false;
            }

            let statusTextContent = i18n.config_loaded || '完成';
            let tokenHtml = '';
            try {
                const usage = await pywebview.api.get_last_usage();
                if (usage && usage.prompt_tokens !== undefined) {
                    tokenHtml = ` | <span style="color:#000;font-weight:500;">Tokens：${usage.prompt_tokens}（输入）+${usage.completion_tokens}（输出）</span>`;
                }
            } catch(e) {}
            statusText.innerHTML = statusTextContent + tokenHtml;
        }

        function startPolling() {
            if (replyTimer) { clearInterval(replyTimer); replyTimer = null; }
            if (reasoningTimer) { clearInterval(reasoningTimer); reasoningTimer = null; }
            if (pollingTimer) { clearInterval(pollingTimer); pollingTimer = null; }
            pendingReply = '';
            pendingReasoning = '';
            waitCount = 0;

            isStreaming = true;
            fullReply = '';
            fullReasoning = '';
            isStopped = false;
            currentAssistantEl = null;

            const thinkVal = document.getElementById('think-select').value;
            const showReasoning = (thinkVal !== '关') && document.getElementById('show-reasoning-check').checked;
            const div = createAssistantMessage();
            if (!showReasoning) {
                div._reasoningDetails.style.display = 'none';
            }
            chatDiv.appendChild(div);
            currentAssistantEl = div;
            scrollToBottomIfNeeded();

            pollingTimer = setInterval(async () => {
                try {
                    const chunk = await pywebview.api.get_next_chunk();
                    if (chunk === null) {
                        clearInterval(pollingTimer);
                        pollingTimer = null;
                        finishStream();
                        return;
                    }
                    if (chunk === '__WAIT__') {
                        waitCount++;
                        if (waitCount > MAX_WAIT) {
                            clearInterval(pollingTimer);
                            pollingTimer = null;
                            showError('生成超时，请重试');
                            isStreaming = false;
                            isWaiting = false;
                            setInputEnabled(true);
                        }
                        return;
                    }
                    waitCount = 0;
                    if (chunk.startsWith('__ERROR__:')) {
                        let errorMsg = chunk.substring(10);
                        let displayMsg = errorMsg;
                        if (errorMsg.includes('|')) {
                            const parts = errorMsg.split('|');
                            const code = parts[0];
                            const msg = parts[1];
                            displayMsg = `错误 ${code}: ${msg}`;
                        } else {
                            displayMsg = `错误: ${errorMsg}`;
                        }
                        clearInterval(pollingTimer);
                        pollingTimer = null;
                        showError(displayMsg);
                        isStreaming = false;
                        isWaiting = false;
                        setInputEnabled(true);
                        return;
                    }
                    if (chunk.startsWith('__REASONING__:')) {
                        if (currentAssistantEl._reasoningEl && currentAssistantEl._reasoningEl.style.display !== 'none') {
                            const r = chunk.substring(14);
                            fullReasoning += r;
                            pendingReasoning += r;
                            if (!reasoningTimer) {
                                reasoningTimer = setInterval(typeReasoningChar, 10);
                            }
                        }
                    } else {
                        fullReply += chunk;
                        pendingReply += chunk;
                        if (!replyTimer) {
                            replyTimer = setInterval(typeReplyChar, 10);
                        }
                    }
                } catch (e) {
                    clearInterval(pollingTimer);
                    pollingTimer = null;
                    showError('轮询错误: ' + e.message);
                    isStreaming = false;
                    isWaiting = false;
                    setInputEnabled(true);
                }
            }, 50);
        }


        async function stopGeneration() {
            if (isStreaming || isWaiting) {
                try {
                    await pywebview.api.stop_generation();
                    isStopped = true;
                    clearInterval(pollingTimer); pollingTimer = null;
                    if (reasoningTimer) clearInterval(reasoningTimer);
                    if (replyTimer) clearInterval(replyTimer);
                    if (currentAssistantEl) {
                        const rEl = currentAssistantEl._reasoningEl;
                        const pEl = currentAssistantEl._replyEl;
                        if (rEl && rEl.dataset.raw) rEl.textContent = rEl.dataset.raw;
                        if (pEl && pEl.dataset.raw) pEl.innerHTML = renderContent(pEl.dataset.raw);
                        else if (pEl) pEl.textContent = i18n.stopped || '已停止';
                        const copyBtn = currentAssistantEl._copyBtn;
                        if (copyBtn) copyBtn.style.display = 'inline-block';
                    }
                    isStreaming = false; isWaiting = false; setInputEnabled(true);
                    removeLoadingMessage();
                    showToast(i18n.generation_stopped || '已停止生成');
                } catch(e) { showToast('停止失败: ' + e.message); }
            }
        }


        async function sendMessage() {
            const text = userInput.value.trim();
            if (selectedFiles.length === 0 && !text) {
                showToast(i18n.no_file_or_text || '请选择文件或输入文本'); return;
            }
            addUserMessage(text, selectedFiles);
            const filesToSend = selectedFiles.map(f => ({ name: f.name, size: f.size, type: f.type, data: f.data }));
            const fileCount_ = selectedFiles.length;
            selectedFiles = []; updateFileBadges(); userInput.value = '';
            isWaiting = true; setInputEnabled(false); addLoadingMessage();
            try {
                let uploadedFiles = [];
                if (filesToSend.length > 0) {
                    uploadedFiles = await pywebview.api.upload_files(filesToSend);
                }
                const result = await pywebview.api.send_message(text, uploadedFiles);
                if (result && result.startsWith('__ERROR__:')) {
                    let errorMsg = result.substring(10);
                    let displayMsg = errorMsg;
                    if (errorMsg.includes('|')) {
                        const parts = errorMsg.split('|');
                        const code = parts[0];
                        const msg = parts[1];
                        displayMsg = `错误 ${code}: ${msg}`;
                    } else {
                        displayMsg = `错误: ${errorMsg}`;
                    }
                    removeLoadingMessage();
                    showError(displayMsg);
                    isWaiting = false; setInputEnabled(true);
                    return;
                }
                setStatus(i18n.send_files ? i18n.send_files.replace('{count}', fileCount_) : `已发送 ${fileCount_} 个文件`);
                startPolling();
            } catch(e) {
                removeLoadingMessage(); showError('发送失败: ' + e.message);
                isWaiting = false; setInputEnabled(true);
            }
        }


        async function readFileAsDataURL(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = (e) => resolve(e.target.result.split(',')[1]);
                reader.onerror = (e) => reject(e.target.error);
                reader.readAsDataURL(file);
            });
        }

        async function handleFiles(fileList) {
            const allowed = ['txt','py','json','csv','css','html','md','pdf','docx','xlsx'];
            let added = 0;
            for (const file of fileList) {
                if (file.size > 10 * 1024 * 1024) {
                    showToast(i18n.file_too_large_msg ? i18n.file_too_large_msg.replace('{name}', file.name) : `文件过大: ${file.name}`);
                    continue;
                }
                const ext = file.name.split('.').pop().toLowerCase();
                if (!allowed.includes(ext)) {
                    showToast(i18n.unsupported_format ? i18n.unsupported_format.replace('{name}', file.name).replace('{ext}', ext) : `不支持: ${file.name}`);
                    continue;
                }
                try {
                    const data = await readFileAsDataURL(file);
                    selectedFiles.push({ name: file.name, size: file.size, type: ext, data: data });
                    added++;
                } catch(err) {
                    showToast(i18n.read_error ? i18n.read_error.replace('{name}', file.name).replace('{error}', err.message) : `读取失败: ${file.name}`);
                }
            }
            if (added > 0) {
                updateFileBadges();
                showToast(i18n.added_files ? i18n.added_files.replace('{count}', added) : `已添加 ${added} 个文件`);
                userInput.focus();
            }
            fileInput.value = '';
        }

        function updateFileBadges() {
            if (selectedFiles.length === 0) {
                fileBadges.innerHTML = '';
                fileCount.textContent = '';
                return;
            }
            let html = '';
            selectedFiles.forEach((f, idx) => {
                html += `<span class="file-badge">📄 ${f.name} (${formatSize(f.size)})<span class="remove" data-index="${idx}">✕</span></span>`;
            });
            fileBadges.innerHTML = html;
            fileCount.textContent = `${selectedFiles.length} 个文件`;
            fileBadges.querySelectorAll('.remove').forEach(el => {
                el.addEventListener('click', function(e) {
                    e.stopPropagation();
                    const idx = parseInt(this.dataset.index);
                    selectedFiles.splice(idx, 1);
                    updateFileBadges();
                    showToast(i18n.file_removed || '已移除文件');
                });
            });
        }


        document.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
            const inputArea = document.getElementById('input-area');
            if (inputArea) inputArea.style.background = '#e8f0fe';
        });

        document.addEventListener('dragleave', function(e) {
            e.preventDefault();
            const inputArea = document.getElementById('input-area');
            if (inputArea) inputArea.style.background = '';
        });

        document.addEventListener('drop', function(e) {
            e.preventDefault();
            const inputArea = document.getElementById('input-area');
            if (inputArea) inputArea.style.background = '';
            if (e.dataTransfer && e.dataTransfer.files.length > 0) {
                handleFiles(e.dataTransfer.files);
            }
        });


        function refreshText() {
            const allMessages = chatDiv.querySelectorAll('.message');
            allMessages.forEach(msg => {
                const rEl = msg.querySelector('.reasoning-box');
                const pEl = msg.querySelector('.reply-box');
                // 不再处理用户消息（避免二次渲染）
                if (rEl && rEl.dataset.raw) rEl.textContent = rEl.dataset.raw;
                if (pEl && pEl.dataset.raw) pEl.innerHTML = renderContent(pEl.dataset.raw);
            });
            showToast(i18n.refresh_text || '已刷新');
        }

        function resetPage() {
            closeExternal();
            if (isStreaming || isWaiting) {
                if (!confirm(i18n.reset_confirm || '确定重置页面吗？')) return;
                isStreaming = false; isWaiting = false;
                if (reasoningTimer) clearInterval(reasoningTimer);
                if (replyTimer) clearInterval(replyTimer);
                if (pollingTimer) clearInterval(pollingTimer);
            }
            chatDiv.innerHTML = '';
            messages = [];
            currentAssistantEl = null;
            selectedFiles = [];
            updateFileBadges();
            setInputEnabled(true);
            setStatus(i18n.reset_done || '已重置');
            showToast(i18n.reset_done || '页面已重置');
            loadHistory();
        }

        async function loadHistory() {
            try {
                const history = await pywebview.api.get_initial_messages();
                if (history && history.length) {
                    messages = history;
                    for (const msg of messages) {
                        const div = document.createElement('div');
                        div.className = 'message';
                        if (msg.role === 'user') {
                            const escaped = (msg.content || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                            div.innerHTML = `<div class="user-msg"><div class="user-text" style="white-space:pre-wrap;">${escaped}</div></div>`;
                        } else {
                            let html = '<div class="assistant-msg">';
                            if (msg.reasoning_content) {
                                html += `<details class="reasoning-details" open>
                                            <summary>${i18n.reasoning_title || '思考过程'}</summary>
                                            <div class="reasoning-box">${renderContent(msg.reasoning_content)}</div>
                                         </details>`;
                            }
                            html += `<div class="assistant-text">${renderContent(msg.content)}</div></div>`;
                            div.innerHTML = html;
                        }
                        chatDiv.appendChild(div);
                    }
                }
                const memoryText = await pywebview.api.get_memory_content();
                if (memoryText) {
                    const div = document.createElement('div');
                    div.className = 'message assistant-msg';
                    div.innerHTML = `<div class="assistant-text" style="background:#f0f0f0;color:#666;font-size:0.9em;">${i18n.load_memory || '已加载记忆'}</div>`;
                    chatDiv.appendChild(div);
                }
            } catch(e) { console.warn('加载历史失败:', e); }
        }


        const externalViewer = document.getElementById('external-viewer');
        const externalIframe = document.getElementById('external-iframe');
        const externalBackBtn = document.getElementById('external-back-btn');

        function openExternal(url) {
            closeExternal();
            setTimeout(() => {
                const separator = url.includes('?') ? '&' : '?';
                const finalUrl = url + separator + '_t=' + Date.now();
                externalIframe.src = finalUrl;
                externalViewer.style.display = 'flex';
                userInput.disabled = true;
                sendBtn.disabled = true;
                uploadBtn.disabled = true;
                stopBtn.style.display = 'none';
            }, 50);
        }

        function openHTMLContent(htmlContent) {
            if (!htmlContent || !htmlContent.trim()) return;
            let fullHtml = htmlContent;
            if (!htmlContent.toLowerCase().includes('<!doctype') && !htmlContent.toLowerCase().includes('<html')) {
                fullHtml = `<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HTML Preview</title>
</head>
<body>
${htmlContent}
</body>
</html>`;
            }
            const encoded = encodeURIComponent(fullHtml);
            const dataUri = 'data:text/html;charset=utf-8,' + encoded;
            openExternal(dataUri);
        }

        function closeExternal() {
            externalIframe.src = '';
            externalViewer.style.display = 'none';
            userInput.disabled = false;
            sendBtn.disabled = false;
            uploadBtn.disabled = false;
            if (!isStreaming && !isWaiting) {
                stopBtn.style.display = 'none';
            } else {
                stopBtn.style.display = 'inline-block';
            }
            userInput.focus();
        }

        externalBackBtn.addEventListener('click', closeExternal);

        sendBtn.addEventListener('click', sendMessage);
        stopBtn.addEventListener('click', stopGeneration);

        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                if (e.ctrlKey || e.shiftKey) {
                    e.preventDefault();
                    const start = userInput.selectionStart;
                    const end = userInput.selectionEnd;
                    const val = userInput.value;
                    userInput.value = val.substring(0, start) + '\n' + val.substring(end);
                    userInput.selectionStart = userInput.selectionEnd = start + 1;
                    userInput.dispatchEvent(new Event('input', { bubbles: true }));
                } else {
                    e.preventDefault();
                    sendMessage();
                }
            }
        });

        uploadBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => { if (e.target.files.length > 0) handleFiles(e.target.files); });
        document.addEventListener('paste', (e) => {
            const files = [];
            for (const item of e.clipboardData.items) {
                if (item.kind === 'file') files.push(item.getAsFile());
            }
            if (files.length > 0) {
                e.preventDefault();
                e.stopPropagation();
                handleFiles(files);
            }
        });

        document.getElementById('refresh-text-btn').addEventListener('click', refreshText);
        document.getElementById('reset-page-btn').addEventListener('click', resetPage);


        async function fetchModels() {
            const statusEl = document.getElementById('fetch-status');
            if (!statusEl) return;
            const apiBase = document.getElementById('api-base-input')?.value.trim() || 'https://api.deepseek.com';
            statusEl.textContent = '加载中...';
            try {
                const result = await pywebview.api.get_models_with_base(apiBase);
                if (result && result.error) {
                    statusEl.textContent = result.error;
                    return;
                }
                if (!Array.isArray(result) || result.length === 0) {
                    statusEl.textContent = '未获取到模型列表';
                    return;
                }
                const select = document.getElementById('model-select');
                if (!select) return;
                select.innerHTML = '';
                for (const m of result) {
                    const opt = document.createElement('option');
                    opt.value = m.id || m;
                    opt.textContent = m.id || m;
                    select.appendChild(opt);
                }
                const config = await pywebview.api.get_config();
                const currentModel = config.model || 'deepseek-v4-flash';
                if (result.some(m => (m.id || m) === currentModel)) {
                    select.value = currentModel;
                } else if (result.length > 0) {
                    select.value = result[0].id || result[0];
                }
                statusEl.textContent = (i18n.fetch_models_success || '已获取 {count} 个模型').replace('{count}', result.length);
            } catch(e) {
                statusEl.textContent = (i18n.fetch_models_error || '获取模型列表失败: {error}').replace('{error}', e.message || e);
            }
        }

        document.getElementById('apply-api-btn').addEventListener('click', async () => {
            const apiBase = document.getElementById('api-base-input').value.trim() || 'https://api.deepseek.com';
            try {
                const config = await pywebview.api.get_config();
                config.api_base = apiBase;
                await pywebview.api.save_config(config);
                showToast('API 地址已保存，请更换密钥');
                setTimeout(() => {
                    document.getElementById('key-btn').click();
                }, 500);
            } catch(e) {
                showToast('保存失败: ' + e.message);
            }
        });

        settingsBtn.addEventListener('click', async () => {
            try {
                const config = await pywebview.api.get_config();
                currentLang = config.language || 'zh_Cn';
                document.getElementById('lang-select').value = currentLang;
                document.getElementById('model-select').value = config.model || 'deepseek-v4-flash';
                document.getElementById('think-select').value = config.think || '关';
                document.getElementById('memory-check').checked = config.memory || false;
                document.getElementById('web-search-check').checked = config.web_search || false;
                document.getElementById('advanced-toggle').checked = config.advanced_enabled || false;
                if (config.advanced_enabled) advancedSection.classList.add('show');
                else advancedSection.classList.remove('show');
                document.getElementById('temperature-slider').value = Math.round((config.temperature || 1.0) * 10);
                document.getElementById('temperature-value').textContent = (config.temperature || 1.0).toFixed(1);
                document.getElementById('max-tokens-input').value = config.max_tokens || 65536;
                document.getElementById('logprobs-check').checked = config.logprobs || false;
                document.getElementById('top-logprobs-input').value = config.top_logprobs || 0;
                document.getElementById('show-reasoning-check').checked = config.show_reasoning !== undefined ? config.show_reasoning : true;
                document.getElementById('json-mode-check').checked = config.json_mode || false;
                document.getElementById('stop-sequences-input').value = config.stop_sequences || '';
                document.getElementById('user-id-input').value = config.user_id || '';
                document.getElementById('memory-mode-select').value = config.memory_mode || 'full';
                document.getElementById('max-rounds-input').value = config.max_rounds || 10;
                document.getElementById('api-base-input').value = config.api_base || 'https://api.deepseek.com';
                document.getElementById('custom-model-input').value = config.custom_model || '';
                document.getElementById('encryption-method-select').value = config.encryption_method || 'win32crypt';

                if (await pywebview.api.has_api_key()) {
                    fetchModels();
                } else {
                    document.getElementById('fetch-status').textContent = i18n.api_key_required_for_models || '请先设置 API 密钥';
                }
                updateMutualExclusion();
                settingsModal.style.display = 'block';
            } catch(e) { showToast('加载设置失败: ' + e.message); }
        });

        document.getElementById('fetch-models-btn').addEventListener('click', fetchModels);

        document.getElementById('settings-save').addEventListener('click', async () => {
            const newLang = document.getElementById('lang-select').value;
            const advancedEnabled = document.getElementById('advanced-toggle').checked;
            const newConfig = {
                language: newLang,
                model: document.getElementById('model-select').value,
                think: document.getElementById('think-select').value,
                memory: document.getElementById('memory-check').checked,
                web_search: document.getElementById('web-search-check').checked,
                advanced_enabled: advancedEnabled,
                temperature: advancedEnabled ? parseFloat(document.getElementById('temperature-value').textContent) : 1.0,
                max_tokens: advancedEnabled ? parseInt(document.getElementById('max-tokens-input').value) || 32767:32767,
                logprobs: advancedEnabled ? document.getElementById('logprobs-check').checked : false,
                top_logprobs: advancedEnabled ? parseInt(document.getElementById('top-logprobs-input').value) || 0 : 0,
                show_reasoning: advancedEnabled ? document.getElementById('show-reasoning-check').checked : true,
                json_mode: advancedEnabled ? document.getElementById('json-mode-check').checked : false,
                stop_sequences: advancedEnabled ? document.getElementById('stop-sequences-input').value.trim() : '',
                user_id: advancedEnabled ? document.getElementById('user-id-input').value.trim() : '',
                memory_mode: document.getElementById('memory-mode-select').value,
                max_rounds: parseInt(document.getElementById('max-rounds-input').value) || 10,
                api_base: document.getElementById('api-base-input').value.trim() || 'https://api.deepseek.com',
                custom_model: document.getElementById('custom-model-input').value.trim(),
                encryption_method: document.getElementById('encryption-method-select').value,
            };

            try {
                await pywebview.api.save_config(newConfig);
                settingsModal.style.display = 'none';
                if (currentLang !== newLang) {
                    if (confirm(i18n.language_changed_restart || '语言已更改，需要重启程序生效。是否立即重启？')) {
                        await pywebview.api.restart_app();
                    }
                } else {
                    showToast(i18n.config_saved || '设置已保存');
                    fetchModels();
                }
            } catch(e) { showToast('保存失败: ' + e.message); }
        });

        document.getElementById('settings-cancel').addEventListener('click', () => {
            settingsModal.style.display = 'none';
        });

        document.getElementById('clear-memory-btn').addEventListener('click', async () => {
            if (confirm('确定清除记忆吗？')) {
                try {
                    const result = await pywebview.api.clear_memory();
                    showToast(result ? '记忆已清除' : '记忆文件不存在');
                } catch(e) { showToast('清除失败: ' + e.message); }
            }
        });

        document.getElementById('clear-cache-btn').addEventListener('click', async () => {
            if (confirm('确定清除所有缓存吗？\n这将删除所有配置、记忆和API密钥，程序将自动退出。')) {
                try {
                    const result = await pywebview.api.clear_all_cache();
                    showToast(result);
                    setTimeout(() => {
                        window.close();
                    }, 1500);
                } catch(e) {
                    showToast('清除失败: ' + e.message);
                }
            }
        });

        function updateMutualExclusion() {
            const isThink = document.getElementById('think-select').value !== '关';
            const tempSlider = document.getElementById('temperature-slider');
            const logprobsCheck = document.getElementById('logprobs-check');
            const topLogprobsInput = document.getElementById('top-logprobs-input');
            tempSlider.disabled = isThink;
            if (isThink) {
                if (!tempSlider.parentElement.querySelector('.disabled-text')) {
                    const span = document.createElement('span');
                    span.className = 'disabled-text';
                    span.textContent = ' ';
                    tempSlider.parentElement.appendChild(span);
                }
            } else {
                const dt = tempSlider.parentElement.querySelector('.disabled-text');
                if (dt) dt.remove();
            }
            logprobsCheck.disabled = isThink;
            if (isThink) {
                if (!logprobsCheck.parentElement.querySelector('.disabled-text')) {
                    const span = document.createElement('span');
                    span.className = 'disabled-text';
                    span.textContent = '(思考模式下无效)';
                    logprobsCheck.parentElement.appendChild(span);
                }
            } else {
                const dt = logprobsCheck.parentElement.querySelector('.disabled-text');
                if (dt) dt.remove();
            }
            topLogprobsInput.disabled = !(logprobsCheck.checked && !isThink);
        }

        document.getElementById('think-select').addEventListener('change', updateMutualExclusion);
        document.getElementById('logprobs-check').addEventListener('change', updateMutualExclusion);
        document.getElementById('temperature-slider').addEventListener('input', function() {
            document.getElementById('temperature-value').textContent = (this.value / 10).toFixed(1);
        });

        keyBtn.addEventListener('click', async () => {
            const modal = document.createElement('div');
            modal.style.cssText = 'position:fixed;z-index:2000;left:0;top:0;width:100%;height:100%;background:rgba(0,0,0,0.4);display:flex;justify-content:center;align-items:center;';
            modal.innerHTML = `
                <div style="background:#fff;padding:20px;border-radius:8px;width:400px;max-width:90%;">
                    <h3>更换API密钥</h3>
                    <input id="new-key-input" type="password" placeholder="请输入新的API密钥" style="width:100%;padding:8px;margin:12px 0;border:1px solid #ddd;border-radius:4px;">
                    <div style="display:flex;gap:8px;flex-wrap:wrap;">
                        <button id="key-confirm-btn" style="padding:6px 16px;background:#007aff;color:#fff;border:none;border-radius:4px;cursor:pointer;">确定</button>
                        <button id="key-get-btn" style="padding:6px 16px;background:#34c759;color:#fff;border:none;border-radius:4px;cursor:pointer;">获取密钥</button>
                        <button id="key-cancel-btn" style="padding:6px 16px;background:#6c757d;color:#fff;border:none;border-radius:4px;cursor:pointer;">取消</button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);

            document.getElementById('key-get-btn').addEventListener('click', function() {
                window.open('https://platform.deepseek.com/', '_blank');
            });

            document.getElementById('key-confirm-btn').addEventListener('click', async function() {
                const newKey = document.getElementById('new-key-input').value.trim();
                if (newKey) {
                    try {
                        const success = await pywebview.api.change_api_key(newKey);
                        if (success) {
                            showToast('API密钥更新成功');
                            modal.remove();
                            setStatus('密钥已设置，就绪');
                            if (typeof fetchModels === 'function') {
                                fetchModels();
                            }
                        } else {
                            showToast('密钥无效，请重试');
                            document.getElementById('new-key-input').value = '';
                            document.getElementById('new-key-input').focus();
                        }
                    } catch(e) {
                        showToast('更新失败: ' + e.message);
                    }
                }
            });

            document.getElementById('key-cancel-btn').addEventListener('click', function() {
                modal.remove();
            });

            modal.addEventListener('click', function(e) {
                if (e.target === modal) modal.remove();
            });
        });


        document.addEventListener('click', function(e) {
            const btn = e.target.closest('.copy-btn');
            if (btn) {
                const code = btn.dataset.code;
                if (code) {
                    const rawCode = decodeURIComponent(code);
                    (navigator.clipboard && navigator.clipboard.writeText) ?
                        navigator.clipboard.writeText(rawCode).then(() => showToast(i18n.copy_success || '已复制')).catch(() => fallbackCopy(rawCode)) :
                        fallbackCopy(rawCode);
                }
            }
        });

        function fallbackCopy(text) {
            const ta = document.createElement('textarea');
            ta.value = text;
            document.body.appendChild(ta);
            ta.select();
            try { document.execCommand('copy'); showToast(i18n.copy_success || '已复制'); }
            catch(e) { showToast('复制失败'); }
            document.body.removeChild(ta);
        }

        advancedToggle.addEventListener('change', function() {
            if (this.checked) {
                advancedSection.classList.add('show');
            } else {
                advancedSection.classList.remove('show');
            }
        });

        const aboutModal = document.getElementById('about-modal');
        document.getElementById('about-btn').addEventListener('click', function() {
            aboutModal.style.display = 'block';
        });
        document.getElementById('about-close-btn').addEventListener('click', function() {
            aboutModal.style.display = 'none';
        });
        aboutModal.addEventListener('click', function(e) {
            if (e.target === aboutModal) aboutModal.style.display = 'none';
        });


        window.onerror = function(message, source, lineno, colno, error) {
            const errorMsg = `JS错误: ${message}\n位置: ${source}:${lineno}:${colno}\n堆栈: ${error ? error.stack : '无'}`;
            console.error(errorMsg);
            try { pywebview.api.log_frontend_error(errorMsg); } catch(e) {}
            return true;
        };

        window.addEventListener('unhandledrejection', function(e) {
            const errorMsg = `未处理的 Promise 拒绝: ${e.reason}`;
            console.error(errorMsg);
            try { pywebview.api.log_frontend_error(errorMsg); } catch(err) {}
        });


        window.addEventListener('pywebviewready', async function() {
            try {
                const config = await pywebview.api.get_config();
                currentLang = config.language || 'zh_Cn';
                loadI18n(currentLang);
                document.getElementById('model-select').value = config.model || 'deepseek-v4-flash';
                document.getElementById('think-select').value = config.think || '关';
                document.getElementById('memory-check').checked = config.memory || false;
                document.getElementById('web-search-check').checked = config.web_search || false;
                document.getElementById('show-reasoning-check').checked = config.show_reasoning !== false;

                const hasKey = await pywebview.api.has_api_key();
                if (!hasKey) {
                    setTimeout(() => {
                        document.getElementById('key-btn').click();
                    }, 300);
                } else {
                    fetchModels();
                }

                loadingOverlay.style.display = 'none';
                appContainer.style.display = 'flex';
                await loadHistory();
                userInput.disabled = false;
                setInputEnabled(true);
                setStatus(i18n.config_loaded || '就绪');
            } catch(e) {
                console.error('初始化失败', e);
                loadingOverlay.style.display = 'none';
                appContainer.style.display = 'flex';
                showError('初始化失败: ' + e.message);
            }
        });


        function showNetworkError(msg) {
            let el = document.getElementById('network-status');
            if (!el) {
                el = document.createElement('div');
                el.id = 'network-status';
                el.style.cssText = 'position:fixed;bottom:70px;left:50%;transform:translateX(-50%);background:#dc3545;color:#fff;padding:8px 20px;border-radius:20px;z-index:9999;font-size:13px;box-shadow:0 2px 10px rgba(0,0,0,0.3);';
                document.body.appendChild(el);
            }
            el.textContent = msg;
            el.style.display = 'block';
        }

        function hideNetworkError() {
            const el = document.getElementById('network-status');
            if (el) el.style.display = 'none';
        }

        function rerenderAllMessages() {
            if (!chatDiv) return;
            const isAtBottom = chatDiv.scrollHeight - chatDiv.scrollTop - chatDiv.clientHeight < 10;
            chatDiv.innerHTML = '';
            if (messages && messages.length > 0) {
                for (const msg of messages) {
                    const div = document.createElement('div');
                    div.className = 'message';
                        if (msg.role === 'user') {
                            const escaped = (msg.content || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                            div.innerHTML = `<div class="user-msg"><div class="user-text" style="white-space:pre-wrap;">${escaped}</div></div>`;
                        } else {
                            let html = '<div class="assistant-msg">';
                            if (msg.reasoning_content) {
                                html += `<details class="reasoning-details" open>
                                            <summary>${i18n.reasoning_title || '思考过程'}</summary>
                                            <div class="reasoning-box">${renderContent(msg.reasoning_content)}</div>
                                         </details>`;
                            }
                            html += `<div class="assistant-text">${renderContent(msg.content)}</div></div>`;
                            div.innerHTML = html;
                        }                    chatDiv.appendChild(div);
                }
            }
            if (isAtBottom) {
                chatDiv.scrollTop = chatDiv.scrollHeight;
            }
        }

        function reloadCDN() {
            if (typeof marked === 'undefined') {
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
                document.head.appendChild(script);
            }
            if (typeof katex === 'undefined') {
                if (!document.querySelector('link[href*="katex.min.css"]')) {
                    const link = document.createElement('link');
                    link.rel = 'stylesheet';
                    link.href = 'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css';
                    document.head.appendChild(link);
                }
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js';
                document.head.appendChild(script);
            }
            let retries = 0;
            const waitForLoad = setInterval(() => {
                if (typeof marked !== 'undefined' && typeof katex !== 'undefined') {
                    clearInterval(waitForLoad);
                    hideNetworkError();
                    rerenderAllMessages();
                }
                retries++;
                if (retries > 30) {
                    clearInterval(waitForLoad);
                    showNetworkError('CDN 资源加载超时，请手动刷新页面');
                }
            }, 500);
        }

        function checkCDN() {
            const missing = [];
            if (typeof marked === 'undefined') missing.push('marked');
            if (typeof katex === 'undefined') missing.push('katex');
            if (missing.length === 0) {
                hideNetworkError();
                return true;
            } else {
                showNetworkError('网络已恢复，正在重新加载资源...');
                reloadCDN();
                return false;
            }
        }

        setInterval(() => {
            if (navigator.onLine) {
                if (typeof marked === 'undefined' || typeof katex === 'undefined') {
                    checkCDN();
                } else {
                    hideNetworkError();
                }
            } else {
                showNetworkError('ERROR：网络已断开，请检查网络连接');
            }
        }, 3000);

        setTimeout(() => {
            if (navigator.onLine) {
                if (typeof marked === 'undefined' || typeof katex === 'undefined') {
                    checkCDN();
                }
            }
        }, 1000);
    </script>
</body>
</html>
'''

def main():
    try:
        app = DeepSeekWebViewApp()
        window = webview.create_window(
            app.strings['title'],
            html=HTML_TEMPLATE,
            width=1000,
            height=700,
            resizable=True,
            min_size=(600, 400)
        )

        window.expose(app.get_initial_messages)
        window.expose(app.get_memory_content)
        window.expose(app.send_message)
        window.expose(app.stop_generation)
        window.expose(app.get_next_chunk)
        window.expose(app.get_full_reply)
        window.expose(app.get_full_reasoning)
        window.expose(app.get_config)
        window.expose(app.save_config)
        window.expose(app.clear_memory)
        window.expose(app.change_api_key)
        window.expose(app.restart_app)
        window.expose(app.upload_files)
        window.expose(app.get_last_usage)
        window.expose(app.get_balance)
        window.expose(app.clear_all_cache)
        window.expose(app.has_api_key)
        window.expose(app.log_frontend_error)
        window.expose(app.get_models_with_base)
        window.expose(app.get_models)

        app.window = window
        webview.start()
    except Exception as e:
        import traceback
        from datetime import datetime
        error_msg = traceback.format_exc()
        crash_log_path = os.path.join(APP_DIR, 'crash_log.txt')
        with open(crash_log_path, 'w', encoding='utf-8') as f:
            f.write(f"=== 程序崩溃时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            f.write(error_msg)
        try:
            webview.create_window(
                '程序崩溃',
                html=f'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>程序崩溃</title>
<style>
body {{ font-family: sans-serif; padding: 20px; }}
h2 {{ color: #dc3545; }}
pre {{ background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 12px; color: #333; }}
.path {{ background: #e8f0fe; padding: 6px 12px; border-radius: 4px; font-family: monospace; font-size: 13px; }}
</style>
</head>
<body>
<h2>程序发生错误</h2>
<p>错误详情已写入：</p>
<p class="path">{crash_log_path}</p>
<pre>{error_msg[:600]}</pre>
<p style="color:#999;font-size:12px;margin-top:12px;">关闭此窗口后程序将退出</p>
</body>
</html>''',
                width=650,
                height=480
            ).start()
        except:
            print(f"程序崩溃，日志已写入: {crash_log_path}")
            print(error_msg)
            input("按 Enter 键退出...")
        sys.exit(1)

if __name__ == '__main__':
    main()
