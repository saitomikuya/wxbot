## **插件开发指南**
本框架采用 **异步消息总线** + **智能Core** 的设计，极大地简化了开发流程。开发者无需关心底层的 Protocol 协议、并发控制或昵称查询，只需专注于业务逻辑。

### 1. 快速开始

所有的插件都存放在 `plugins/` 目录下。要创建一个新插件（例如 `echo_bot`），请按照以下结构创建文件：

Plaintext

```
plugins/
└── echo_bot/
    └── __init__.py  <-- 插件入口
```

**最小代码示例：**

Python

```
# plugins/echo_bot/__init__.py
class Plugin:
    def on_message(self, msg_type, data, service):
        # 1. 过滤非文本消息 (11046 = 文本)
        if msg_type != 11046: 
            return
        
        # 2. 获取基础信息
        room_wxid = data.get('room_wxid') # 群ID
        content = data.get('msg', '')     # 内容
        
        # 3. 业务逻辑：如果是 "ping"
        if content == "ping":
            # 4. 调用 SDK 发送
            service.send_text(room_wxid, "pong!")
```

### 2. `service` 对象能力速查

`service` 对象是插件与微信交互的唯一桥梁，提供了以下核心方法：

#### A. 智能判断 @我

**`service.is_at_me(room_wxid, content)`**

- **功能**：判断消息是否在 @机器人。
    
- **智能点**：
    
    - 自动识别机器人在该群的昵称（无需写死）。
        
    - 如果是刚进群，会自动等待 1.5秒 等待昵称学习完成。
        
    - 自动去除 `@名字` 和多余的空格。
        
- **返回值**：如果是 @我，返回**去除名字后的真实内容**；否则返回 `False`。
    

#### B. 智能引用回复 (推荐)

**`service.send_smart_at(room_wxid, to_wxid, text_content)`**

- **功能**：发送带 @ 的回复消息。
    
- **智能点**：
    
    - 会自动查询 `to_wxid` 的群内昵称。
        
    - 如果查到了，显示 `@真实昵称 回复内容`。
        
    - 如果没查到（或超时），自动使用 `{$@}` 占位符确保蓝字提醒。
        
- **参数**：
    
    - `to_wxid`: 对方的 wxid（从 data['from_wxid'] 获取）。
        
    - `text_content`: 回复的文本。
        

#### C. 基础发送

**`service.send_text(room_wxid, content)`**

- **功能**：发送普通文本。
    
- **适用**：不需要 @ 人的场景，如定时播报。
    

### 3. 高级开发技巧

#### 并发与阻塞

主程序已内置 `ThreadPoolExecutor`。

- **可以阻塞**：你可以在 `on_message` 里直接请求（requests），耗时 30秒 也没关系，**不会卡死**机器人的其他回复。
    
- **无需手动开线程**：除非你需要执行定时任务或死循环监听。
    

#### 获取配置信息

机器人自身的 ID 存放在 `service.bot_wxid` 中，这由 `config.json` 统一管理。