"""招呼语生成器"""
from .client import DeepSeekClient
from .prompts import GREETING_PROMPT, GREETING_USER


class Greeter:
    def __init__(self, client: DeepSeekClient, resume_summary: str):
        self.client = client
        self.resume_summary = resume_summary

    def generate(self, job: dict, match_result: dict) -> str:
        """生成个性化招呼语"""
        user_prompt = GREETING_USER.format(
            resume_summary=self.resume_summary,
            job_title=job.get("job_name", ""),
            company=job.get("company", job.get("brand", "")),
            score=match_result.get("score", 0),
            match_points=", ".join(match_result.get("skill_overlap", [])[:5]),
            greeting_points=", ".join(match_result.get("greeting_points", [])[:3]),
        )

        greeting = self.client.chat_with_retry(
            system_prompt=GREETING_PROMPT,
            user_prompt=user_prompt,
            temperature=0.8,
            max_tokens=512,
        )

        return greeting.strip().strip('"').strip("'")
