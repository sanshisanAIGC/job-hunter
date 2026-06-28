# AI 求职助手 (AI Job Hunter)

> Boss直聘自动求职系统 — AI搜索岗位 + 简历匹配评分 + 招呼语生成 + 自动投递

## 功能

- **岗位搜索**：基于 boss-agent-cli 自动搜索 Boss直聘岗位
- **AI 匹配**：DeepSeek 驱动的简历-JD 深度匹配，逐岗评分（0-100）
- **招呼语生成**：根据匹配结果自动生成个性化招呼语
- **收藏管理**：高匹配岗位自动收藏到本地候选池
- **消息监控**：自动检测 HR 新消息，AI 生成回复
- **飞书通知**：高匹配岗位即时推送、每日求职报告

## 架构

```
简历(PDF/文本) → DeepSeek 解析 → 结构化画像
                                    ↓
boss-agent-cli → search → 岗位列表 → DeepSeek 匹配评分
                                    ↓
                              ≥阈值 → 招呼语生成 → 自动投递
                                    ↓
                              chatmsg → 新消息检测 → AI 回复
                                    ↓
                              飞书通知
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt boss-agent-cli
patchright install chromium

# 2. 配置 .env
cp .env.example .env
# 填入 DeepSeek API Key 和飞书凭证

# 3. 登录 Boss直聘
boss login --cookie-source edge

# 4. 解析简历
python main.py setup --resume "你的简历文本"

# 5. 运行搜索+匹配
python main.py run

# 6. 查看收藏
boss shortlist list
```

## 依赖

- **boss-agent-cli**：Boss直聘 CLI 工具（搜索、投递、聊天）
- **DeepSeek v4 Pro**：简历解析 + JD匹配 + 招呼语生成
- **飞书开放平台**：消息通知

## 飞书应用权限

- `docx:document` — 文档读写
- `im:message:send_as_bot` — 发送消息通知

## 安全提示

- `.env` 包含 API 密钥，已加入 .gitignore
- `data/` 包含简历和投递记录，已加入 .gitignore
- Boss直聘风控严格，建议搜索间隔 ≥30秒，每日投递 ≤50

## License

MIT
