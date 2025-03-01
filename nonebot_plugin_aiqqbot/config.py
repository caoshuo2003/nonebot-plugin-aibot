from typing import Optional
from nonebot import get_plugin_config
from pydantic import BaseModel, Field

class Config(BaseModel):
    openai_api_key: Optional[str] = Field(default=None)
    openai_endpoint: Optional[str] = Field(default=None)
    gpt_model: Optional[str] = Field(default=None)
    max_tokens: Optional[int] = Field(default=2048)
    presets_location: Optional[str] = Field(default="./presets/")

plugin_config: Config = get_plugin_config(Config)

OPENAI_API_KEY = plugin_config.openai_api_key
OPENAI_ENDPOINT = plugin_config.openai_endpoint
GPT_MODEL = plugin_config.gpt_model
MAX_TOKENS = plugin_config.max_tokens
PRESETS_LOCATION = plugin_config.presets_location
