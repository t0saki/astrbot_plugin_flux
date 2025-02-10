from astrbot.api.message_components import *
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import aiohttp
import asyncio

@register("mod-flux", "", "使用Flux.1文生图。使用 /aimg <提示词> 生成图片。", "1.3")
class ModFlux(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.api_key = config.get("api_key")
        self.model = config.get("model")
        self.num_inference_steps = config.get("num_inference_steps")
        self.size = config.get("size")
        self.api_url = "https://api.siliconflow.cn/v1/images/generations"

        if not self.api_key:
            raise ValueError("API密钥必须配置")

    @filter.command("aimg")
    async def generate_image(self, event: AstrMessageEvent):

        full_message = event.message_obj.message_str
        parts = full_message.split(" ", 1)
        prompt = parts[1].strip() if len(parts) > 1 else ""

        if not self.api_key:
            yield event.plain_result("\n请先在配置文件中设置API密钥")
            return

        if not prompt:
            yield event.plain_result("\n请提供提示词！使用方法：/aimg <提示词>")
            return

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_key}'
                }
                
                data = {
                    "prompt": prompt,
                    "model": self.model,
                    "size": self.size,
                    "num_inference_steps": self.num_inference_steps,
                    "prompt_enhancement": True
                }
                
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    response_data = await response.json()

                    if response.status != 200:
                        yield event.plain_result(f"\n生成图片失败: {response_data.get('error', '未知错误')}")
                        return
                    
                    image_url = response_data['data'][0]['url']
                    
                    chain = [
                        Plain(f"prompt：{prompt}\n生成中~~~~~~"),
                        Image.fromURL(image_url)
                    ]
                    
                    yield event.chain_result(chain)
            
        except Exception as e:
            yield event.plain_result(f"\n生成图片失败: {str(e)}")
