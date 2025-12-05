# plugins/toutiao/__init__.py
import requests
import time
from datetime import datetime

class Plugin:
    def __init__(self):
        # 头条热榜 API
        self.api_url = "https://api.toutiaoapi.com/hot-event/hot-board/?client_extra_params=%7B%22custom_log_pb%22:%22%7B%5C%22category_name%5C%22:%5C%22hotboard_light%5C%22,%5C%22entrance_hotspot%5C%22:%5C%22search%5C%22,%5C%22location%5C%22:%5C%22hot_board%5C%22,%5C%22style_id%5C%22:%5C%2240030%5C%22%7D%22%7D&count=50&log_pb=%7B%22category_name%22:%22hotboard_light%22,%22entrance_hotspot%22:%22search%22,%22location%22:%22hot_board%22,%22style_id%22:%2240030%22%7D&only_hot_list=1&tab_name=stream&enter_keyword=%E4%B8%AD%E6%97%A5%E5%B0%B1%E6%A0%B8%E6%B1%A1%E6%9F%93%E6%B0%B4%E6%8E%92%E6%B5%B7%E9%97%AE%E9%A2%98%E8%BE%BE%E6%88%90%E5%85%B1%E8%AF%86&origin=hot_board"

    def fetch_hot_list(self):
        """同步获取热榜数据 (Requests版)"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        for _ in range(3):  # 重试机制
            try:
                response = requests.get(self.api_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                print(f"[Toutiao] 获取失败，重试中... {e}")
                time.sleep(1)
        return None

    def on_message(self, msg_type, data, service):
        # 1. 仅处理文本消息 (11046)
        if msg_type != 11046:
            return

        # 2. 解析内容
        content = data.get('msg', '').strip()
        room_wxid = data.get('room_wxid') # 可能是群ID，也可能是私聊的个人ID
        
        # 3. 触发指令判断
        if content.lower() in ['头条', 'toutiao', '热榜']:
            # 获取数据
            hot_data = self.fetch_hot_list()
            
            if hot_data and 'data' in hot_data:
                # 提取前 10 条
                items = hot_data['data'][:10]
                titles = [item.get('Title', '未知标题') for item in items]
                
                # 获取当前时间
                current_time = datetime.now().strftime("%H:%M:%S")
                
                # 拼接回复文本
                reply_text = f"【头条热榜】{current_time}\n" + "\n".join([f"{i+1}. {title}" for i, title in enumerate(titles)])
                
                # 4. 发送消息
                service.send_text(room_wxid, reply_text)
            else:
                # 失败时可选反馈，防止无响应
                service.send_text(room_wxid, "获取热榜失败，请稍后再试。")
