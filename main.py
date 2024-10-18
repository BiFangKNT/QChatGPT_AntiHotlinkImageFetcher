# -*- coding: utf-8 -*-
import requests
from pkg.plugin.models import *
from pkg.plugin.host import EventContext, PluginHost
import re
from mirai import Image, Plain

@register(name="AntiHotlinkImageFetcher", description="根据关键词输入，自动处理防盗链图片链接，转为图片输出",
          version="1.0",
          author="BiFangKNT")
class AntiHotlinkImageFetcherPlugin(Plugin):

    def __init__(self, plugin_host: PluginHost):
        super().__init__(plugin_host)
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

        headers = self.get_pixiv_headers()
        cookies = self.get_pixiv_cookies()

        try:
            response = requests.get(api_url, headers=headers, cookies=cookies)
            response.raise_for_status()  # 检查请求是否成功
            data = response.json()

            # 检查返回的 JSON 是否有正确的结构
            if 'body' in data and 'urls' in data['body'] and 'original' in data['body']['urls']:
                image_url = data['body']['urls']['original']
                return image_url
            else:
                return None

        except requests.RequestException as e:
            print(f"网络请求失败: {str(e)}")
            return None

    def get_pixiv_headers(self):
        """返回 Pixiv 请求的必要 Headers"""
        return {
            'Referer': 'https://www.pixiv.net',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }

    def get_pixiv_cookies(self):
        """
        返回 Pixiv 请求的必要 Cookies，替换为你的实际 Cookies。

        获取方法:
        1. 打开 Pixiv 网站并登录。
        2. 打开浏览器的开发者工具 (F12)。
        3. 刷新页面并在网络 (Network) 面板中筛选 "ajax" 请求。
        4. 查找与 pid 相关的请求，查看该请求的 Cookies 并逐项复制。
        """
        return {
            'PHPSESSID': '',  # 替换为实际的 PHPSESSID
            '__cf_bm': '',  # 替换为你的实际值
            'cf_clearance': '',  # 替换为你的实际值
            'yuid_b': '',  # 替换为你的实际值
        }

    def __del__(self):
        pass
