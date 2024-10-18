import json
import requests
from urllib.parse import urlparse
from pkg.plugin.models import *
from pkg.plugin.host import EventContext, PluginHost
import re
from mirai import Image, Plain
import os

@register(name="AntiHotlinkImageFetcher", description="根据关键词输入，自动处理防盗链图片链接，转为图片输出",
          version="1.0",
          author="BiFangKNT")
class AntiHotlinkImageFetcherPlugin(Plugin):

    def __init__(self, plugin_host: PluginHost):
        super().__init__(plugin_host)
        self.config = self.load_config()
        self.url_pattern = re.compile(r'[a-zA-Z0-9]+[:：]\d+')

    @on(NormalMessageResponded)
    def optimize_message(self, event: EventContext, **kwargs):
        original_message = kwargs['response_text']

        # 如果正则表达式没有匹配成功，直接终止脚本执行
        if not self.url_pattern.search(original_message):
            return

        optimized_message = self.convert_message(original_message)

        if optimized_message:
            event.add_return('reply', optimized_message)

    def load_config(self):
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(plugin_dir, 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def convert_message(self, message):
        parts = []
        last_end = 0

        for match in self.url_pattern.finditer(message):
            start, end = match.span()
            if start > last_end:
                parts.append(Plain(message[last_end:start]))

            matched_text = match.group()
            site_keyword, pid = re.split(r'[:：]', matched_text, 1)
            site_keyword = site_keyword.strip()
            pid = pid.strip()

            if site_keyword == "pixiv":
                # 调用 Pixiv 图片获取函数
                try:
                    image_url = self.fetch_pixiv_image_url(pid)
                    if image_url:
                        parts.append(Image(url=image_url))
                    else:
                        parts.append(Plain(f"未找到图片 URL\n"))
                except Exception:
                    parts.append(Plain(f"链接无法访问，请检查 URL 是否正确。\n"))
                    parts.append(Plain(matched_text))
            else:
                parts.append(Plain(f"未找到站点配置: {site_keyword}\n"))

            last_end = end

        if last_end < len(message):
            parts.append(Plain(message[last_end:]))

        return parts if parts else message

    def fetch_pixiv_image_url(self, pid):
        """根据 Pixiv 作品 ID 获取原始图片 URL"""
        api_url = f"https://www.pixiv.net/ajax/illust/{pid}"
        headers = {
            'Referer': 'https://www.pixiv.net',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }

        response = requests.get(api_url, headers=headers)
        response.raise_for_status()

        data = response.json()
        # 从 JSON 数据中提取原始图片 URL
        image_url = data['body']['urls']['original']

        return image_url

    def __del__(self):
        pass
