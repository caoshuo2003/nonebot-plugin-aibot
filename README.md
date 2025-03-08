# nonebot-plugin-aiqqbot

_✨ QQ中可以读图的聊天的机器人 ✨_

## 📖 介绍

由于手机qq发送图片时不可携带消息，所以这里可以先发送图片，AI处理后回复“已收到”，然后可以继续聊天对话。

## 💿 安装

<details open>
<summary>使用 nb-cli 安装(未实现)</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-aiqqbot

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

    pip install nonebot-plugin-aiqqbot
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_aiqqbot"]

</details>

## ⚙️ 配置

使用localstore插件查看并填写下表中的必填配置

| 配置项 | 必填 | 默认值 | 说明 |
|:-----:|:----:|:----:|:----:|
| OPENAI_API_KEY | 是 | 无 | API密钥 |
| OPENAI_ENDPOINT | 是 | 无 | API服务端点 |
| GPT_MODEL | 是 | 无 | 调用的GPT模型 |
| MAX_TOKENS | 否 | 2048 | 回复的最大token |
| PRESETS_LOCATION| 否 | ./presets/ | 默认情况请在bot.py目录下创建presets文件夹 |

## 🎉 使用
### 指令表
| 指令 |  需要@ | 范围 | 说明 |
|:-----:|:----:|:----:|:----:|
| 重置会话 | 是 | 群聊/私聊 | 清楚会话记忆，恢复初始预设 |
| 加载预设 | 是 | 群聊/私聊 | 加载设定，目前有catgirl，nvyou, kua，default|

请使用前查询localstore并在data.dir建立presets文件夹，必须有default预设！！！重置会话会加载default预设。
其他预设来源:
+ 从github仓库下载
+ 自行创建预设名

