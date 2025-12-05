# -*- coding: utf8 -*-
import logging

logger = logging.getLogger('Plugin.IDResponder')

class Plugin:
    def on_message(self, msg_type, data, service):
        if msg_type != 11046:
            return

        content = data.get('msg') or data.get('content') or ""
        
        if content.strip().lower() == "test":
            from_wxid = data.get('from_wxid')
            room_wxid = data.get('room_wxid')
            
            # 优先回复群，否则回复人
            target_wxid = room_wxid if room_wxid else from_wxid
            reply_text = f"{target_wxid}"
            
            if target_wxid:
                logger.info(f"插件触发，准备回复: {target_wxid}")
                service.send_text(target_wxid, reply_text)
