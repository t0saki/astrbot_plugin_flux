from astrbot.api.message_components import *
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import aiohttp
import asyncio
import random
import json

@register("mod-flux", "", "使用Flux.1文生图。使用 /aimg <提示词> 生成图片。", "1.4")
class ModFlux(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.api_key = config.get("api_key")
        self.model = config.get("model")
        self.num_inference_steps = config.get("num_inference_steps")
        self.size = config.get("size")
        self.api_url = config.get("api_url")
        self.seed = config.get("seed")
        self.enable_translation = config.get("enable_translation")  # 保留此配置项以维持兼容性

        if not self.api_key:
            raise ValueError("API密钥必须配置")

    @filter.command("aimg")
    async def generate_image(self, event: AstrMessageEvent):
        # 1. 获取用户输入的提示词
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
            # 获取种子ID - 修复种子处理逻辑
            try:
                if self.seed == "随机" or not self.seed:
                    current_seed = random.randint(1, 2147483647)
                else:
                    current_seed = int(self.seed)
            except (ValueError, TypeError):
                # 如果转换失败，使用随机种子
                current_seed = random.randint(1, 2147483647)

            # 调用文生图API
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
                    "prompt_enhancement": True,
                    "seed": current_seed
                }
                
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    response_data = await response.json()
                    if response.status != 200:
                        # 修复response_data可能不是字典的问题
                        error_msg = "未知错误"
                        if isinstance(response_data, dict) and "error" in response_data:
                            error_msg = response_data["error"]
                        yield event.plain_result(f"\n生成图片失败: {error_msg}")
                        return

                    # 确保response_data是字典且包含预期的键
                    if not isinstance(response_data, dict) or "data" not in response_data or not response_data["data"]:
                        yield event.plain_result("\n生成图片失败: API返回格式异常")
                        return
                        
                    image_url = response_data['data'][0]['url']
                    chain = [
                        Plain(f"提示词：{prompt}\nseed ID：{current_seed}\n生成中~~~~~~"),
                        Image.fromURL(image_url)
                    ]
                    yield event.chain_result(chain)

        except Exception as e:
            yield event.plain_result(f"\n生成图片失败: {str(e)}")
