# plugins/bubble_counter/__init__.py

class Plugin:
    def on_message(self, msg_type, data, service):
        """
        数泡泡插件
        """
        # 1. 过滤非文本消息 (Protocol 11046 = 文本)
        if msg_type != 11046:
            return
        
        # 2. 获取基础信息
        content = data.get('msg', '')      # 消息内容
        room_wxid = data.get('room_wxid')  # 群ID
        
        # 如果没有内容，或者不在群里(room_wxid为空)，通常不处理
        if not content or not room_wxid:
            return

        # 3. 业务逻辑：检查消息内容是否全是中文句号
        # 注意：all("") 返回 True，所以上面必须先检查 if not content
        if all(char == '。' for char in content):
            bubble_count = len(content)
            response = f"{bubble_count}个泡泡"
            
            # 4. 调用 SDK 发送
            service.send_text(room_wxid, response)
            
