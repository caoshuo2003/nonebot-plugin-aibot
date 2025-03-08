import asyncio
import aiocron
import io
import os
import socket
import base64
import time
import httpx
import json

from openai import OpenAI
from nonebot import get_plugin_config, on_command, on_message, get_driver, get_bot
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message, PrivateMessageEvent, GroupMessageEvent
from nonebot.params import CommandArg
from nonebot.rule import Rule
from nonebot.typing import T_State
from nonebot.log import logger
from typing import Dict
from .config import Config, DEFAULT_CONFIG
from pathlib import Path
from nonebot import require
require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store

# 插件元数据
__plugin_meta__ = PluginMetadata(
    name="aiqqbot",
    description="A plugin that can recognize pictures and reply to chats with AI",
    usage="Send a picture or message",
    type="application",
    homepage="https://github.com/caoshuo2003/nonebot-plugin-aiqqbot",
    config=Config,
    supported_adapters={"~onebot.v11"}
)
driver = get_driver()
CONFIG_FILE = None
plugin_data_dir = None

# 初始化全局配置变量为空，后续在启动时赋值
plugin_config: Config = None
OPENAI_API_KEY = None
OPENAI_ENDPOINT = None
GPT_MODEL = None
MAX_TOKENS = None
PRESETS_LOCATION = None
client = None 

async def init_config_file() -> None:
    global CONFIG_FILE, plugin_data_dir
    logger.info("初始化ing")
    await asyncio.sleep(3)
    if CONFIG_FILE is None:
        CONFIG_FILE = store.get_plugin_config_file("aiqqbot_plugin_config.json")
        plugin_data_dir = store.get_plugin_data_dir()
    if not CONFIG_FILE.exists():
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(DEFAULT_CONFIG, indent=4, ensure_ascii=False))
        logger.info(f"配置文件已生成: {CONFIG_FILE}")
    else:
        logger.info(f"配置文件已存在: {CONFIG_FILE}")

def load_config() -> Config:
    config_data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return Config(**config_data)

@driver.on_startup
async def startup() -> None:
    global client, plugin_config, OPENAI_API_KEY, OPENAI_ENDPOINT, GPT_MODEL, MAX_TOKENS, PRESETS_LOCATION
    # 延迟初始化配置文件，确保插件上下文已正确设置
    await init_config_file()
    plugin_config = load_config()
    OPENAI_API_KEY = plugin_config.openai_api_key
    OPENAI_ENDPOINT = plugin_config.openai_endpoint
    GPT_MODEL = plugin_config.gpt_model
    MAX_TOKENS = plugin_config.max_tokens
    PRESETS_LOCATION = plugin_data_dir + "presets/"
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_ENDPOINT
    )
    logger.info("插件启动完成，OpenAI 客户端已初始化。")
# 初始化 OpenAI API
# openai.api_key = OPENAI_API_KEY
# openai.api_base = OPENAI_ENDPOINT

# 初始化 session 存储
sessions = {}

# 读取预设
def read_presets_txt(preset_name):
    if preset_name != "default":
        file_path = PRESETS_LOCATION + preset_name + ".txt"
    else:
        file_path = PRESETS_LOCATION + "default.txt"
    # logger.info(f"加载文件名 {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError as e:
        logger.info(f"没有这个预设哦")
        return ""
    file_content = ""
    for line in lines:
        if line.strip():
            file_content += line.strip()
    prompts = {"role": "system", "content": file_content}
    return prompts

# 清理过期的会话
def clean_expired_sessions():
    """清理过期的会话"""
    current_time = time.time()
    expired_sessions = [session_id for session_id, data in sessions.items() if current_time - data['start_time'] > 3600]
    for session_id in expired_sessions:
        del sessions[session_id]

# 处理私聊消息
def is_private_message() -> Rule:
    return Rule(lambda bot, event: isinstance(event, PrivateMessageEvent))

private_message = on_message(rule=is_private_message(), priority=6, block=True)

@private_message.handle()
async def handle_private_message(bot:Bot, event: PrivateMessageEvent, presets="default"):
    user_id = str(event.user_id)
    await handle_message(bot, event, user_id, presets)

# 处理群聊消息
def is_group_message() -> Rule:
    return Rule(lambda bot, event: isinstance(event, GroupMessageEvent))

group_message = on_message(rule=is_group_message(), priority=6, block=True)

@group_message.handle()
async def handle_group_message(bot: Bot, event: GroupMessageEvent, presets="default"):
    if event.is_tome():
        group_id = str(event.group_id)
        await handle_message(bot, event, group_id, presets)

async def handle_message(bot: Bot, event: MessageEvent, session_id: str, presets: str):
    clean_expired_sessions()
    if session_id not in sessions:
        sessions[session_id] = {"messages": [], "contextual_memory": True, "start_time": time.time(), "presets": presets}
        sessions[session_id]["messages"].append(read_presets_txt(presets))

    if event.message[0].type == "image":
        image_url = event.message[0].data["url"]
        question = "请记住这张图片, 只需回复'我已经了解了这张图片，有什么问题吗？'"
        reply =  await analyze_image(image_url, question, session_id)
        await bot.send(event, reply)
    else:
        user_input = event.get_plaintext().strip()
        sessions[session_id]["messages"].append({"role": "user", "content": user_input})
        try:
            reply = await chat_openai(session_id)
            if reply:
                await bot.send(event, reply)
            else: 
                await bot.send(event, f"出错了，请尝试“重置会话”哦qvq")
        except Exception as e:
            logger.error(f"OpenAI API 请求失败: {e}")
            await bot.send(event, "目前无法回复您的问题。")

async def chat_openai(session_id: str) -> str:
    try:
        contextual_memory = sessions[session_id]["contextual_memory"]
        # logger.info(f"contextual_memory: {contextual_memory}")
        # logger.info(f"session_id: {session_id}")
        if contextual_memory:
            selected_messages = sessions[session_id]["messages"]
            #if not check_max_tokens(selected_messages, 4096):
             #   return ""
        else:
            selected_messages = [sessions[session_id]["messages"][-1]]
        
        # logger.info(selected_messages)
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=selected_messages,
            max_tokens=MAX_TOKENS
        )
        reply = response.choices[0].message.content
        sessions[session_id]["messages"].append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        logger.error(f"Openai fail: {e}")

async def analyze_image(image_url: str, question: str, session_id: str) -> str:
    try:
        # 将图像编码为 base64
        base64_image =  await encode_image(image_url)

        # 调用API处理图像
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                                 }
            ],
            max_tokens=MAX_TOKENS
        )
        reply = response.choices[0].message.content
        # reply = response.choices[0].message['content']
        sessions[session_id]["messages"].append({"role": "user", "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            }
                        }
                    ]})
        return reply
    except Exception as e:
        logger.error(f"Error analysing image: {e}")

async def encode_image(image_url):
    async with httpx.AsyncClient() as client:
        for i in range(3):
            try:
                resp = await client.get(image_url, timeout=20)
                resp.raise_for_status()
                return base64.b64encode(resp.content).decode('utf-8')
            except Exception as e:
                logger.warning(f"Error downloading {image_url}, retry {i}/3: {e}")
                await asyncio.sleep(3)
# 重置会话
handle_clear_session = on_command("重置会话", priority=5, block=True)

@handle_clear_session.handle()
async def clear_session_handler(bot: Bot, event: PrivateMessageEvent | GroupMessageEvent):
    # 根据事件类型选择对应的标识符
    if isinstance(event, PrivateMessageEvent):
        identifier = str(event.user_id)
        session_type = "私聊"
    elif isinstance(event, GroupMessageEvent):
        identifier = str(event.group_id)
        session_type = "群聊"
    else:
        return
    await clear_session(identifier)
    await bot.send(event, f"{session_type}会话清除。")

async def clear_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
'''
handle_enable_private_memory = on_command("开启记忆", rule=is_private_message(), priority=5, block=True)

@handle_enable_private_memory.handle()
async def enable_private_memory(bot: Bot, event: PrivateMessageEvent):
    user_id = str(event.user_id)
    await enable_memory(user_id)
    await bot.send(event, "私聊记忆开启。")

# 开启记忆
handle_enable_group_memory = on_command("开启记忆", rule=is_group_message(), priority=5, block=True)

@handle_enable_group_memory.handle()
async def enable_group_memory(bot: Bot, event: GroupMessageEvent):
    group_id = str(event.group_id)
    await enable_memory(group_id)
    await bot.send(event, "Group记忆开启。")


async def enable_memory(session_id):
    sessions[session_id] = {"messages": [], "contextual_memory": True, "start_time": time.time()}
    sessions[session_id]["messages"].append(read_presets_txt("default"))
'''
# 加载预设
handle_presets_session = on_command("加载预设", priority=5, block=True)

@handle_presets_session.handle()
async def handle_preset_private_receive(bot: Bot, event: PrivateMessageEvent, args: Message = CommandArg()):
    # 获取命令的参数
    presets = args.extract_plain_text().strip()
    if isinstance(event, PrivateMessageEvent):
        identifier = str(event.user_id)
        session_type = "私聊"
    elif isinstance(event, GroupMessageEvent):
        identifier = str(event.group_id)
        session_type = "群聊"
    presets_content = read_presets_txt(presets)
    if not presets_content:
        await bot.send(event, f"预设加载失败, 请确定预设名称是否正确!")
        return
    
    if identifier not in sessions:
        sessions[user_id] = {"messages": [], "contextual_memory": True, "start_time": time.time(), "presets": presets}
        sessions[user_id]["messages"].append(presets_content)
    else:
        sessions[user_id]["messages"] = []
        sessions[user_id]["contextual_memory"] = True
        sessions[user_id]["messages"].append(presets_content)
    await bot.send(event, f"预设加载成功!")
            
