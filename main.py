import json
import requests
from lxml import html
from pkg.plugin.models import *
from pkg.plugin.host import EventContext, PluginHost
from mirai import Image, Plain
import os
import re


@register(name="AntiHotlinkImageFetcher", description="根据关键词输入，自动处理防盗链图片链接，转为图片输出", version="1.0",
          author="BiFangKNT")
class AntiHotlinkImageFetcherPlugin(Plugin):

    def __init__(self, plugin_host: PluginHost):
        super().__init__(plugin_host)
        # 获取当前插件所在目录的绝对路径
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        # 构造 config.json 文件的路径，确保从插件目录中加载
        config_path = os.path.join(plugin_dir, 'config.json')
        # 读取配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    @on(NormalMessageResponded)
    def handle_message(self, event: EventContext, **kwargs):
        user_message = kwargs['response_text']
        # 检查是否符合关键词输入格式，如：pixiv:10086 或 pixiv：10086
        if re.match(r'^[^\s]+[:：]\d+$', user_message):  # 这里是正确的正则表达式
            site_keyword, pid = re.split(r'[:：]', user_message, 1)
            site_keyword = site_keyword.strip()
            pid = pid.strip()

            # 根据关键词从 config 中找到对应站点的配置
            if site_keyword in self.config:
                site_config = self.config[site_keyword]
                domain = site_config['domain']
                url_suffix = site_config['url_suffix']
                xpath = site_config['xpath']

                # 构建图片 URL
                full_url = f"https://{domain}{url_suffix}{pid}"
                try:
                    # 获取图片页面
                    headers = {
                        'Referer': f"https://{domain}",
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
                    }
                    response = requests.get(full_url, headers=headers)
                    response.raise_for_status()

                    # 解析 HTML 并查找图片链接
                    tree = html.fromstring(response.content)
                    img_element = tree.xpath(xpath)
                    if img_element and 'src' in img_element[0].attrib:
                        img_url = img_element[0].attrib['src']

                        # 如果图片链接是相对链接，补全为完整链接
                        if img_url.startswith('//'):
                            img_url = 'https:' + img_url

                        # 使用图片 URL 发送图片
                        event.add_return('reply', Image(url=img_url))
                    else:
                        # 如果找不到图片元素
                        event.add_return('reply',
                                         Plain(f"未找到指定的图片，检查 XPath 或者图片页面可能已变更。URL：{full_url}"))

                except requests.RequestException as e:
                    # 请求失败的处理
                    event.add_return('reply', Plain(f"请求失败，错误信息：{str(e)}，URL：{full_url}"))
            else:
                # 如果配置文件中没有找到对应的站点
                event.add_return('reply', Plain(f"未找到指定的站点配置：{site_keyword}"))
        else:
            # 如果输入格式不正确
            event.add_return('reply', Plain("输入格式不正确，正确格式为：站点关键词：PID，例如 'pixiv：10086'"))

    def __del__(self):
        pass
