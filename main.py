from astrbot.api.message_components import *
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import requests

@register("mod-flux", "", "使用Flux.1文生图。使用 /aimg <提示词> 生成图片。", "1.0")
class FluxImageGenerator(Star):
    def __init__(self, ctx: Context, cfg: dict):
        super().__init__(ctx)
        self.api_key = cfg.get("api_key")
        self.model_name = "black-forest-labs/FLUX.1-dev"  # 将模型名称写死在这里
        self.base_url = "https://api.siliconflow.cn"
        self.endpoint = "/v1/images/generations"
        self.full_url = f"{self.base_url}{self.endpoint}"

        if not self.api_key:
            raise ValueError("API密钥必须配置")

    @filter.command("aimg")
    async def generate_image(self, event: AstrMessageEvent, prompt: str = ""):
        if not self.api_key:
            yield event.plain_result("\n请先在配置文件中设置API密钥")
            return

        if not prompt:
            yield event.plain_result("\n请提供提示词！使用方法：/aimg <提示词>")
            return

        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            payload = {
                "prompt": prompt,
                "model": self.model_name,  # 使用固定的模型名称
                "size": "1024x1024"
            }

            response = requests.post(self.full_url, headers=headers, json=payload)
            response_data = response.json()

            if response.status_code != 200:
                yield event.plain_result(f"\n生成图片失败: {response_data.get('error', '未知错误')}")
                return

            image_url = response_data['data'][0]['url']

            response_chain = [
                Plain(f"prompt：{prompt}\n生成中~~~~~~"),
                Image.fromURL(image_url)
            ]
            
            yield event.chain_result(response_chain)
            
        except Exception as e:
            yield event.plain_result(f"\n生成图片失败: {str(e)}")
