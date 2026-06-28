"""飞书通知模块 — 复用现有飞书应用"""
import httpx


class FeishuNotifier:
    def __init__(self, app_id: str, app_secret: str, open_id: str = ""):
        self.app_id = app_id
        self.app_secret = app_secret
        self.open_id = open_id
        self._token = ""

    def _get_token(self) -> str:
        if self._token:
            return self._token
        resp = httpx.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": self.app_id, "app_secret": self.app_secret},
            timeout=10,
        )
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"飞书认证失败: {data}")
        self._token = data["tenant_access_token"]
        return self._token

    def send_text(self, text: str) -> bool:
        """发送文本消息"""
        if not self.open_id:
            print(f"[Feishu] 未配置通知用户，跳过: {text[:50]}...")
            return False

        token = self._get_token()
        resp = httpx.post(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            params={"receive_id_type": "open_id"},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "receive_id": self.open_id,
                "msg_type": "text",
                "content": json.dumps({"text": text}),
            },
            timeout=10,
        )
        ok = resp.json().get("code") == 0
        if ok:
            print(f"[Feishu] 通知已发送: {text[:50]}...")
        return ok

    def send_card(self, title: str, elements: list[dict]) -> bool:
        """发送卡片消息"""
        if not self.open_id:
            return False

        token = self._get_token()
        card = {
            "header": {"title": {"tag": "plain_text", "content": title}, "template": "blue"},
            "elements": elements,
        }
        resp = httpx.post(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            params={"receive_id_type": "open_id"},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "receive_id": self.open_id,
                "msg_type": "interactive",
                "content": json.dumps(card),
            },
            timeout=10,
        )
        return resp.json().get("code") == 0

    def notify_high_match(self, job: dict, score: int, greeting: str):
        """通知高匹配岗位"""
        text = (
            f"🔥 高匹配岗位 ({score}分)\n"
            f"职位：{job.get('job_name', '')}\n"
            f"公司：{job.get('company', job.get('brand', ''))}\n"
            f"薪资：{job.get('salary', '')}\n"
            f"已自动打招呼：{greeting[:100]}..."
        )
        self.send_text(text)

    def notify_daily_summary(self, stats: dict):
        """每日摘要通知"""
        text = (
            f"📊 求职日报\n"
            f"今日搜索：{stats.get('searched', 0)} 岗位\n"
            f"今日投递：{stats.get('applied', 0)} 个\n"
            f"新消息：{stats.get('new_messages', 0)} 条\n"
            f"面试邀请：{stats.get('interviews', 0)} 个\n"
            f"累计投递：{stats.get('total_applied', 0)} 个"
        )
        self.send_text(text)

    def notify_interview(self, job_name: str, company: str, hr_message: str):
        """通知面试邀请"""
        text = (
            f"🎉 面试邀请！\n"
            f"职位：{job_name}\n"
            f"公司：{company}\n"
            f"HR消息：{hr_message[:150]}"
        )
        self.send_text(text)

    def notify_new_message(self, hr_name: str, message: str, ai_reply: str):
        """通知新消息及AI回复"""
        text = (
            f"💬 新消息\n"
            f"HR：{hr_name}\n"
            f"消息：{message[:100]}\n"
            f"AI已回复：{ai_reply[:100]}"
        )
        self.send_text(text)


import json  # noqa: E402 (用于 send_card 的 json.dumps)
