# plugins/currency_converter/__init__.py
import re
import requests
import json
import logging

# 配置日志
logger = logging.getLogger('CurrencyPlugin')

class Plugin:
    def __init__(self):
        self.api_url = 'http://papi.icbc.com.cn/exchanges/ns/getLatest'
        # 支持的货币列表
        self.supported_currencies = [
            'GBP', 'HKD', 'USD', 'CHF', 'SGD', 'PKR', 'SEK', 'DKK', 'NOK', 
            'JPY', 'CAD', 'AUD', 'MYR', 'EUR', 'RUB', 'MOP', 'THB', 'NZD', 
            'ZAR', 'KZT', 'KRW', 'RMB'
        ]
        # 预编译正则 (格式：100 USD CNY)
        self.pattern = re.compile(r'^(\d+(\.\d+)?)\s+([a-zA-Z]{3})\s+([a-zA-Z]{3})$')

    def on_message(self, msg_type, data, service):
        # 1. 过滤非文本消息
        if msg_type != 11046:
            return

        content = data.get('msg', '').strip()
        room_wxid = data.get('room_wxid') # 群ID

        # 2. 正则匹配
        match = self.pattern.match(content)
        if not match:
            return

        # 3. 解析参数
        try:
            amount = float(match.group(1))
            from_currency = match.group(3).upper()
            to_currency = match.group(4).upper()

            # 别名标准化
            if from_currency == 'CNY': from_currency = 'RMB'
            if to_currency == 'CNY': to_currency = 'RMB'

            # 检查货币支持
            if from_currency not in self.supported_currencies or to_currency not in self.supported_currencies:
                self._send_help(service, room_wxid)
                return

            # 4. 获取汇率
            rates_data = self.get_exchange_rates()
            if not rates_data:
                service.send_text(room_wxid, "无法连接工行接口，请稍后重试。")
                return

            # 5. 计算结果
            result = self.convert_currency(amount, from_currency, to_currency, rates_data['rates'])
            
            if result is not None:
                reply_text = (
                    f"【ICBC {rates_data['publishDate']} {rates_data['publishTime']}】\n"
                    f"{match.group(1)} {from_currency} = {result:.2f} {to_currency}"
                )
                # --- 修改点：使用 send_text 直接发送，不带 @ ---
                service.send_text(room_wxid, reply_text)
            else:
                service.send_text(room_wxid, "汇率转换计算失败。")

        except Exception as e:
            logger.error(f"汇率插件出错: {e}")
            service.send_text(room_wxid, "插件内部错误。")

    def _send_help(self, service, room_wxid):
        """发送支持列表"""
        currencies_str = "、".join(self.supported_currencies)
        msg = f"不支持的货币类型。\n目前支持：{currencies_str}"
        service.send_text(room_wxid, msg)

    def get_exchange_rates(self):
        """同步获取汇率数据"""
        try:
            response = requests.get(self.api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    rates = {item['currencyENName']: float(item['reference']) for item in data['data']}
                    return {
                        'rates': rates,
                        'publishDate': data['data'][0]['publishDate'],
                        'publishTime': data['data'][0]['publishTime']
                    }
        except Exception as e:
            logger.error(f"获取汇率失败: {e}")
        return None

    def convert_currency(self, amount, from_curr, to_curr, rates):
        """计算汇率"""
        try:
            if from_curr == 'RMB':
                if to_curr in rates:
                    return amount / rates[to_curr] * 100
            elif to_curr == 'RMB':
                if from_curr in rates:
                    return amount * rates[from_curr] / 100
            else:
                if from_curr in rates and to_curr in rates:
                    rmb_amount = amount * rates[from_curr] / 100
                    return rmb_amount / rates[to_curr] * 100
        except Exception as e:
            logger.error(f"计算过程出错: {e}")
        return None
