from pydantic import BaseModel
from typing import Dict

class Config(BaseModel):
    openai_api_key: str = "sk-AFMtoBIyM36JzcnAj1MUtwTJQbF0ITsVBqHcYH7CDSDBhVNg"
    openai_endpoint: str = "https://api.chatanywhere.tech"  # 替换为您的自定义端点

class Presets_name:
    # 使用中文名称映射到英文预设名
    preset_mapping: Dict[str, str] = {
        "猫娘": "catgirl",
        "夸夸": "kua",
        "默认": "default",
        "女友": "nvyou"
    }
    @classmethod
    def get_preset_name(cls, chinese_name: str) -> str:
        # 通过中文名称获取英文预设名，如果不存在返回默认提示
        return cls.preset_mapping.get(chinese_name, "default")

# 测试
print(Presets_name.get_preset_name("猫娘"))  # 输出: catgirl
print(Presets_name.get_preset_name("未知"))  # 输出: 未知预设
