"""DeepSeek API 客户端（复用 novel-factory 模式）"""
from openai import OpenAI


class DeepSeekClient:
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com",
                 model: str = "deepseek-v4-pro"):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def chat(self, system_prompt: str, user_prompt: str,
             temperature: float = 0.7, max_tokens: int = 4096,
             disable_thinking: bool = True) -> str:
        extra_body = {"thinking": {"type": "disabled"}} if disable_thinking else {}
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            extra_body=extra_body,
        )
        return response.choices[0].message.content or ""

    def chat_with_retry(self, system_prompt: str, user_prompt: str,
                        max_retries: int = 3, **kwargs) -> str:
        import time
        last_error = None
        for attempt in range(max_retries):
            try:
                return self.chat(system_prompt, user_prompt, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        raise RuntimeError(f"API 调用失败: {last_error}")
