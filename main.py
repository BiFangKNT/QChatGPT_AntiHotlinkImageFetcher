# -*- coding: utf-8 -*-
import requests
from pkg.plugin.context import register, handler, llm_func, BasePlugin, APIHost, EventContext, mirai
from pkg.plugin.events import PersonNormalMessageReceived, GroupNormalMessageReceived  # 导入两个事件类
import re

@register(name="AntiHotlinkImageFetcher", description="根据关键词输入，自动处理防盗链图片链接，转为图片输出",
          version="1.3",
          author="BiFangKNT")
class AntiHotlinkImageFetcherPlugin(BasePlugin):

    def __init__(self, host: APIHost):
        super().__init__(host)
        self.url_pattern = re.compile(r'^[a-zA-Z0-9]+[:：]\d+$')

    # 异步初始化
    async def initialize(self):
        pass

    @handler(PersonNormalMessageReceived)
    @handler(GroupNormalMessageReceived)
    async def on_message(self, ctx: EventContext):
        await self.optimize_message(ctx)

    async def optimize_message(self, ctx: EventContext):

        msg = ctx.event.text_message

        # 输出信息
        self.ap.logger.info(f"反防盗链插件正在处理消息: {msg}")

        # 如果正则表达式没有匹配成功，直接终止脚本执行
        if not self.url_pattern.search(msg):
            self.ap.logger.info("反防盗链插件：格式不匹配，不进行处理")
            return

        optimized_message = self.convert_message(msg)

        if optimized_message:
            # 输出信息
            self.ap.logger.info(f"处理后的消息: {optimized_message}")

            # 回复消息
            ctx.add_return('reply', optimized_message)

            # 阻止该事件默认行为
            ctx.prevent_default()

            # 阻止后续插件执行
            ctx.prevent_postorder()
        else:
            self.ap.logger.info("消息处理后为空，不进行回复")

    def convert_message(self, message):
        parts = []
        last_end = 0

        for match in self.url_pattern.finditer(message):
            start, end = match.span()
            if start > last_end:
                parts.append(mirai.Plain(message[last_end:start]))

            matched_text = match.group()
            site_keyword, pid = re.split(r'[:：]', matched_text, 1)
            site_keyword = site_keyword.strip()
            pid = pid.strip()

            if site_keyword == "pixiv":
                # 调用 Pixiv 图片获取函数
                try:
                    image_url = self.fetch_pixiv_image_url(pid)
                    if image_url:
                        parts.append(mirai.Image(url=image_url))
                        self.ap.logger.info(f"成功获取Pixiv图片: {image_url}")
                    else:
                        parts.append(mirai.Plain(f"未找到图片 URL\n"))
                        self.ap.logger.info(f"未找到Pixiv图片URL: {pid}")
                except Exception as e:
                    parts.append(mirai.Plain(f"链接无法访问，请检查 URL 是否正确。\n"))
                    parts.append(mirai.Plain(matched_text))
                    self.ap.logger.info(f"获取Pixiv图片失败: {str(e)}")
            else:
                parts.append(mirai.Plain(f"未找到站点配置: {site_keyword}\n"))
                self.ap.logger.info(f"未找到站点配置: {site_keyword}")

            last_end = end

        if last_end < len(message):
            parts.append(mirai.Plain(message[last_end:]))

        return parts if parts else None

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
            self.ap.logger.info(f"网络请求失败: {str(e)}")
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
