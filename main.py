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
        self.enable_translation = config.get("enable_translation")  # 直接从配置文件读取

        if not self.api_key:
            raise ValueError("API密钥必须配置")

    async def translate_to_english(self, text: str) -> str:
        """将中文提示词翻译成英文"""
        url = "https://ai.guokei.cn/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer sk-19aCKGVmHjIZCLMwAbBfC4A3Be464433B98e61F564341e2a"
        }
        
        messages = [
            {
                "role": "system",
                "content": """你是一个专业的文生图提示词翻译助手。请将用户输入的中文提示词翻译成适合文生图使用的英文提示词。
                - 对艺术创作类描述，使用更优美和专业的表达
                - 保持图像风格、质量相关的描述词
                - 直接输出翻译结果，不要添加任何解释
                - 如果输入已经是英文，则原样返回
                - 确保翻译结果符合 Stable Diffusion 提示词风格"""
            },
            {
                "role": "user",
                "content": text
            }
        ]
        
        data = {
            "model": "GLM-4-Flash",
            "messages": messages
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content'].strip()
                    return text
        except Exception as e:
            return text

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
            # 2. 如果是中文且翻译开启，调用翻译API
            if self.enable_translation and any('\u4e00' <= char <= '\u9fff' for char in prompt):
                prompt = await self.translate_to_english(prompt)

            # 3. 获取种子ID
            current_seed = random.randint(1, 2147483647) if self.seed == "随机" else int(self.seed)

            # 4. 调用文生图API
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
                        yield event.plain_result(f"\n生成图片失败: {response_data.get('error', '未知错误')}")
                        return

                    image_url = response_data['data'][0]['url']
                    chain = [
                        Plain(f"提示词：{prompt}\nseed ID：{current_seed}\n生成中~~~~~~"),
                        Image.fromURL(image_url)
                    ]
                    yield event.chain_result(chain)

        except Exception as e:
            yield event.plain_result(f"\n生成图片失败: {str(e)}")
