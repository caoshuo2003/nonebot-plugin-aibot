from typing import Optional
from pydantic import BaseModel, Field

class Config(BaseModel):
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API 密钥")
    openai_endpoint: Optional[str] = Field(default="https://api.openai.com", description="OpenAI 接口地址")
    gpt_model: Optional[str] = Field(default="gpt-4o-2024-11-20", description="调用的 GPT 模型")
    max_tokens: Optional[int] = Field(default=2048, description="生成回复的最大 token 数")

DEFAULT_CONFIG = Config().dict()
