# plugins/douyin_hotlist/__init__.py
import requests
import time
import logging
from datetime import datetime, timedelta

# 获取日志记录器，方便调试
logger = logging.getLogger('DouyinPlugin')

class Plugin:
    def __init__(self):
        self.url = "https://aweme.snssdk.com/aweme/v1/hot/search/list/"
        # 伪装 User-Agent 防止被拦截
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def fetch_hotlist(self):
        """
        同步获取抖音热榜数据
        框架已内置线程池，此处可以直接阻塞请求，无需 async
        """
        for _ in range(3):  # 重试 3 次
            try:
                response = requests.get(self.url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.error(f"抖音热榜获取失败: {e}")
                time.sleep(1) # 失败等待1秒
        return None

    def on_message(self, msg_type, data, service):
        """
        SDK 标准入口
        """
        # 1. 仅处理文本消息 (11046)
        if msg_type != 11046:
            return

        # 2. 获取消息内容和群ID
        content = data.get('msg', '').strip()
        room_wxid = data.get('room_wxid')

        # 3. 关键词触发判断
        if content.lower() in ['抖音', 'douyin', '抖音热榜']:
            # 4. 获取数据
            hotlist_data = self.fetch_hotlist()
            
            if hotlist_data:
                try:
                    word_list = hotlist_data.get('data', {}).get('word_list', [])
                    # 按热度排序并取前10
                    top_words = sorted(word_list, key=lambda x: x.get('hot_value', 0), reverse=True)[:10]
                    
                    # 获取当前时间 (UTC+8)
                    current_time = (datetime.utcnow() + timedelta(hours=8)).strftime("%H:%M:%S")
                    
                    # 5. 拼接文案
                    message = f"【抖音热榜】{current_time}\n"
                    for idx, item in enumerate(top_words, 1):
                        word = item.get('word', '未知话题')
                        # 转换热度为"万"单位
                        hot_value = item.get('hot_value', 0) // 10000 
                        message += f"{idx}. {word} [{hot_value}万]\n"
                    
                    # 6. 发送消息
                    service.send_text(room_wxid, message.strip())
                    
                except Exception as e:
                    logger.error(f"数据解析错误: {e}")
                    service.send_text(room_wxid, "获取抖音热榜数据解析失败，请稍后再试。")
            else:
                service.send_text(room_wxid, "网络波动，抖音热榜获取超时。")
