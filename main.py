from astrbot.api.message_components import *
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
import requests
import json

@register("mod-flux", "", "使用Flux.1文生图。使用 /aimg <提示词> 生成图片。", "1.0")
class ModFlux(Star):  # 将类名改为 ModFlux
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.api_key = config.get("api_key")
        self.model = config.get("model")
        self.api_url = config.get("api_url")  # 新增这一行

        # 配置验证
        if not self.api_key or not self.model or not self.api_url:
            raise ValueError("API密钥、模型和请求地址必须配置")

    @filter.command("aimg")
    async def generate_image(self, event: AstrMessageEvent, prompt: str = ""):
        # 检查是否配置了API密钥
        if not self.api_key:
            yield event.plain_result("\n请先在配置文件中设置API密钥")
            return

        # 检查提示词是否为空
        if not prompt:
            yield event.plain_result("\n请提供提示词！使用方法：/aimg <提示词>")
            return

        try:
            # 设置请求头
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'  # 使用配置中的 API 密钥
            }
            
            # 设置请求体，尺寸固定为 1024x1024
            data = {
                "prompt": prompt,
                "model": self.model,
                "size": "1024x1024",  # 尺寸直接写死
                "num_inference_steps": 25,
                "prompt_enhancement": True,
                "seed": 8510
            }
            
            # 发送 POST 请求到配置的 API URL
            response = requests.post(self.api_url, headers=headers, json=data)
            response_data = response.json()

            # 检查响应状态
            if response.status_code != 200:
                yield event.plain_result(f"\n生成图片失败: {response_data.get('error', '未知错误')}")
                return
            
            # 获取生成的图片 URL
            image_url = response_data['data'][0]['url']
            
            # 构建消息链
            chain = [
                Plain(f"prompt：{prompt}\n生成中~~~~~~"),
                Image.fromURL(image_url)
            ]
            
            yield event.chain_result(chain)
            
        except Exception as e:
            yield event.plain_result(f"\n生成图片失败: {str(e)}")
