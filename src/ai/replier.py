"""消息回复生成器"""
import json
from .client import DeepSeekClient
from .prompts import REPLY_PROMPT, REPLY_USER, INTENT_PROMPT, INTENT_USER


class Replier:
    def __init__(self, client: DeepSeekClient, resume_summary: str):
        self.client = client
        self.resume_summary = resume_summary

    def analyze_intent(self, hr_message: str) -> dict:
        """分析 HR 消息意图"""
        resp = self.client.chat_with_retry(
            system_prompt=INTENT_PROMPT,
            user_prompt=INTENT_USER.format(hr_message=hr_message),
            temperature=0.2,
            max_tokens=512,
        )
        try:
            import re
            m = re.search(r'\{.*\}', resp, re.DOTALL)
            if m:
                return json.loads(m.group())
        except json.JSONDecodeError:
            pass
        return {"intent": "other", "urgency": "low", "need_reply": True}

    def generate_reply(self, hr_message: str, chat_history: str = "",
                       has_interview: bool = False, round_count: int = 1) -> str:
        """生成回复"""
        user_prompt = REPLY_USER.format(
            resume_summary=self.resume_summary,
            hr_message=hr_message,
            chat_history=chat_history or "（首次沟通）",
            has_interview="是" if has_interview else "否",
            round_count=round_count,
        )

        reply = self.client.chat_with_retry(
            system_prompt=REPLY_PROMPT,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=1024,
        )

        return reply.strip().strip('"').strip("'")
