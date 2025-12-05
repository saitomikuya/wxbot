# -*- coding: utf8 -*-
import json
import sys
import os
import ctypes
import logging
import time
import threading
from ctypes import WinDLL, WINFUNCTYPE

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s')
logger = logging.getLogger('WeChatCore')

_CURRENT_SOCKET_ID = None
_GLOBAL_RECV_CALLBACK_LIST = []

def c_string(data):
    return ctypes.c_char_p(data.encode('utf-8'))

# --- Ctypes 回调定义 ---
@WINFUNCTYPE(None, ctypes.c_void_p)
def wechat_connect_callback(client_id):
    global _CURRENT_SOCKET_ID
    _CURRENT_SOCKET_ID = client_id
    logger.info(f"Socket已连接: {client_id}")

@WINFUNCTYPE(None, ctypes.c_long, ctypes.c_char_p, ctypes.c_ulong)
def wechat_recv_callback(client_id, data, length):
    if not data: return
    try:
        raw_bytes = ctypes.string_at(data, length)
        json_str = raw_bytes.decode('utf-8', errors='ignore').strip().strip('\x00')
        if not json_str: return
        try:
            dict_data = json.loads(json_str)
        except:
            last_brace = json_str.rfind('}')
            if last_brace != -1:
                dict_data = json.loads(json_str[:last_brace+1])
            else:
                return
        for func in _GLOBAL_RECV_CALLBACK_LIST:
            func(client_id, dict_data.get('type'), dict_data.get('data'))
    except Exception as e:
        logger.error(f"底层回调异常: {e}")

@WINFUNCTYPE(None, ctypes.c_ulong)
def wechat_close_callback(client_id):
    global _CURRENT_SOCKET_ID
    if _CURRENT_SOCKET_ID == client_id:
        _CURRENT_SOCKET_ID = None

class NoveLoader:
    _InitWeChatSocket = 0xB080
    _InjectWeChat = 0xCC10
    _SendWeChatData = 0xAF90
    _DestroyWeChat = 0xC540
    _UseUtf8 = 0xC680
    
    def __init__(self, loader_path):
        if not os.path.exists(loader_path): raise FileNotFoundError(f"DLL缺失: {loader_path}")
        self.loader = WinDLL(loader_path)
        self.base = self.loader._handle
        self._setup_mem()
        self._get_func(self._UseUtf8, None, ctypes.c_bool)()
        self._init_socket()

    def _setup_mem(self):
        try:
            k32 = ctypes.windll.kernel32
            fm = k32.CreateFileMappingA(-1, None, 0x04, 0, 33, b"windows_shell_global__")
            if fm:
                addr = k32.MapViewOfFile(fm, 0x000F001F, 0, 0, 0)
                if addr:
                    key = b"3101b223dca7715b0154924f0eeeee20"
                    ctypes.memmove(addr, ctypes.create_string_buffer(key), len(key))
        except: pass

    def _get_func(self, off, args, res):
        if args is None: args = []
        return ctypes.WINFUNCTYPE(res, *args)(self.base + off)

    def _init_socket(self):
        f = self._get_func(self._InitWeChatSocket, [ctypes.c_void_p]*3, ctypes.c_bool)
        f(wechat_connect_callback, wechat_recv_callback, wechat_close_callback)

    def inject(self, path):
        return self._get_func(self._InjectWeChat, [ctypes.c_char_p], ctypes.c_uint32)(c_string(path))

    def send_data(self, client_id, msg):
        return self._get_func(self._SendWeChatData, [ctypes.c_uint32, ctypes.c_char_p], ctypes.c_bool)(client_id, c_string(msg))

    def destroy(self):
        self._get_func(self._DestroyWeChat, [], ctypes.c_bool)()

# ==========================================
#  ProfileManager (花名册管理器)
# ==========================================
class ProfileManager:
    def __init__(self, service):
        self.service = service
        self._cache = {}
        self._lock = threading.RLock()
        self._query_cooldown = {}

    def get_nick(self, room_wxid, wxid, force_query=True):
        key = f"{room_wxid}_{wxid}"
        with self._lock:
            if key in self._cache:
                val = self._cache[key]
                if val: return val 
        
        if force_query:
            # 占位防止重复查询
            with self._lock:
                if key not in self._cache:
                    self._cache[key] = None 
            self._trigger_query(room_wxid, wxid)
        return None

    def _trigger_query(self, room_wxid, wxid):
        key = f"{room_wxid}_{wxid}"
        now = time.time()
        if now - self._query_cooldown.get(key, 0) < 5: return
        self._query_cooldown[key] = now
        # Protocol 11174
        payload = {"type": 11174, "data": {"room_wxid": room_wxid, "wxid": wxid}}
        self.service.send_payload(payload)

    def wait_for_nick(self, room_wxid, wxid, timeout=1.5):
        """同步阻塞等待昵称"""
        start = time.time()
        while time.time() - start < timeout:
            nick = self.get_nick(room_wxid, wxid, force_query=True)
            if nick: return nick
            time.sleep(0.1)
        return None

# ==========================================
#  WeChatService (SDK核心)
# ==========================================
class WeChatService:
    def __init__(self, loader_path, dll_path, config):
        self.loader_path = loader_path
        self.dll_path = dll_path
        self.config = config
        self.loader = None
        self.msg_handlers = []
        
        # 从配置加载机器人信息
        self.bot_wxid = config.get("bot_wxid", "")
        self.bot_default_name = config.get("bot_default_name", "")
        
        self.profile = ProfileManager(self)

    def register_msg_handler(self, func):
        self.msg_handlers.append(func)

    def _internal_on_recv(self, client_id, msg_type, data):
        if msg_type == 11174:
            self._process_profile_update(data)
        for handler in self.msg_handlers:
            handler(client_id, msg_type, data, self)

    def _process_profile_update(self, data):
        try:
            clist = data.get('contactList', [])
            for c in clist:
                wxid = c.get('userName', {}).get('string')
                nick = c.get('nickName', {}).get('string')
                if wxid and nick:
                    with self.profile._lock:
                        for key in list(self.profile._cache.keys()):
                            if key.endswith(f"_{wxid}"):
                                self.profile._cache[key] = nick
        except: pass

    def start(self):
        try:
            self.loader = NoveLoader(self.loader_path)
            def cb(c, t, d): self._internal_on_recv(c, t, d)
            _GLOBAL_RECV_CALLBACK_LIST.append(cb)
            return bool(self.loader.inject(self.dll_path))
        except Exception as e:
            logger.error(f"启动失败: {e}")
            return False

    def send_payload(self, payload):
        tid = _CURRENT_SOCKET_ID
        if not tid: return False
        return self.loader.send_data(tid, json.dumps(payload, ensure_ascii=False))

    def send_text(self, to_wxid, content):
        """兼容旧插件的基础文本发送 (Protocol 11237)"""
        return self.send_payload({"type": 11237, "data": {"to_wxid": to_wxid, "content": content}})

    def send_at_text(self, room_wxid, content, at_list):
        """发送原生 @ 消息 (Protocol 11240)"""
        return self.send_payload({
            "type": 11240,
            "data": {"to_wxid": room_wxid, "content": content, "at_list": at_list}
        })

    def send_smart_at(self, room_wxid, to_wxid, text_content):
        """[SDK] 智能显名回复：自动查昵称，查不到用 {$@}"""
        nick = self.profile.wait_for_nick(room_wxid, to_wxid, timeout=1.0)
        final_msg = f"@{nick}\u2005\n{text_content}" if nick else f"{{$@}}\n{text_content}"
        self.send_at_text(room_wxid, final_msg, [to_wxid])

    def is_at_me(self, room_wxid, content):
        """[SDK] 智能判断@我：支持自动学习昵称"""
        my_nick = self.profile.get_nick(room_wxid, self.bot_wxid, force_query=True)
        
        if not my_nick and "@" in content:
            my_nick = self.profile.wait_for_nick(room_wxid, self.bot_wxid, timeout=1.5)

        current_name = my_nick if my_nick else self.bot_default_name
        check_str = f"@{current_name}"
        
        if check_str in content:
            return content.replace(check_str, '').replace('\u2005', '').strip()
        return False
