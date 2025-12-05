# -*- coding: utf8 -*-
import os
import json
import sys
import time
import queue
import logging
import importlib
import threading
from concurrent.futures import ThreadPoolExecutor
from wechat_core import WeChatService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MainBot')

class BotManager:
    def __init__(self):
        self.msg_queue = queue.Queue()
        self.plugins = []
        self.service = None
        self.running = True
        self.config = self._load_config()
        self.executor = ThreadPoolExecutor(max_workers=self.config.get("max_workers", 5))

    def _load_config(self):
        """加载 config.json"""
        path = os.path.join(os.path.dirname(__file__), "config.json")
        if not os.path.exists(path):
            logger.error("未找到 config.json，请先创建配置文件！")
            sys.exit(1)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"配置文件读取失败: {e}")
            sys.exit(1)

    def load_plugins(self):
        plugin_dir = os.path.join(os.path.dirname(__file__), "plugins")
        sys.path.insert(0, plugin_dir)
        for item in os.listdir(plugin_dir):
            path = os.path.join(plugin_dir, item)
            if os.path.isdir(path) and os.path.exists(os.path.join(path, '__init__.py')):
                try:
                    module = importlib.import_module(item)
                    if hasattr(module, 'Plugin'):
                        self.plugins.append(module.Plugin())
                        logger.info(f"已加载插件: {item}")
                except Exception as e:
                    logger.error(f"加载插件 {item} 失败: {e}")

    def msg_producer(self, client_id, msg_type, data, service):
        self.msg_queue.put((msg_type, data, service))

    def msg_consumer(self):
        while self.running:
            try:
                msg_type, data, service = self.msg_queue.get(timeout=1)
                self.executor.submit(self._run_plugins, msg_type, data, service)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"消息队列异常: {e}")

    def _run_plugins(self, msg_type, data, service):
        for plugin in self.plugins:
            try:
                plugin.on_message(msg_type, data, service)
            except Exception as e:
                logger.error(f"插件运行错误: {e}")

    def start(self):
        base = os.path.dirname(os.path.abspath(__file__))
        loader = os.path.join(base, self.config.get("dll_loader_name", "Loader_4.1.2.17.dll"))
        dll = os.path.join(base, self.config.get("dll_helper_name", "Helper_4.1.2.17.dll"))

        # 传入 config
        self.service = WeChatService(loader, dll, self.config)
        self.load_plugins()
        self.service.register_msg_handler(self.msg_producer)

        if self.service.start():
            logger.info("服务启动。启动消息消费线程...")
            threading.Thread(target=self.msg_consumer, daemon=True).start()
            try:
                while True: time.sleep(1)
            except KeyboardInterrupt:
                self.running = False
                self.executor.shutdown(wait=False)
        else:
            logger.error("启动失败，请检查DLL路径或微信版本。")

if __name__ == '__main__':
    BotManager().start()
