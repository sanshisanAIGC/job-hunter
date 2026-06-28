"""JD 匹配引擎 — DeepSeek 驱动的简历-JD匹配评分"""
import json
import re
from .client import DeepSeekClient
from .prompts import JD_MATCH_PROMPT, JD_MATCH_USER


class JDMacher:
    def __init__(self, client: DeepSeekClient, resume: dict):
        self.client = client
        self.resume = resume

    def match(self, job: dict) -> dict:
        """
        评估单个岗位的匹配度
        job: {job_name, company, salary, city, description, security_id, ...}
        返回: {score, verdict, skill_overlap, ...}
        """
        resume_json = json.dumps(self.resume, ensure_ascii=False, indent=2)
        job_desc = job.get("description", job.get("job_desc", ""))
        if not job_desc:
            # 尝试从其他字段拼接
            job_desc = job.get("job_name", "") + "\n" + job.get("job_detail", "")

        user_prompt = JD_MATCH_USER.format(
            resume_json=resume_json,
            job_title=job.get("job_name", ""),
            company=job.get("company", job.get("brand", "")),
            salary=job.get("salary", ""),
            city=job.get("city", ""),
            job_description=job_desc[:3000],  # 限制长度
        )

        resp = self.client.chat_with_retry(
            system_prompt=JD_MATCH_PROMPT,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=2048,
        )

        return self._parse_response(resp)

    def _parse_response(self, resp: str) -> dict:
        m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', resp, re.DOTALL)
        if m:
            resp = m.group(1)
        try:
            return json.loads(resp)
        except json.JSONDecodeError:
            start = resp.find('{')
            end = resp.rfind('}')
            if start >= 0 and end > start:
                return json.loads(resp[start:end + 1])
            return {"score": 0, "verdict": "parse_error", "error": resp[:200]}
