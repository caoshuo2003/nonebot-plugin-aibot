from pydantic import BaseModel

class Config(BaseModel):
    openai_api_key: str = ""
    openai_endpoint: str = ""  # 替换为自定义端点
    GPT_MODEL: str = ""
    MAX_TOKEN: int = 2048
