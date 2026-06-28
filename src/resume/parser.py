"""简历解析器 — 文本/PDF → 结构化 JSON"""
import json
import re
from pathlib import Path
from src.ai.prompts import RESUME_PARSE_PROMPT, RESUME_PARSE_USER


class ResumeParser:
    def __init__(self, ai_client):
        self.ai = ai_client

    def parse_text(self, text: str) -> dict:
        """用 DeepSeek 从文本中提取结构化简历信息"""
        prompt = RESUME_PARSE_USER.format(resume_text=text[:8000])

        resp = self.ai.chat_with_retry(
            system_prompt=RESUME_PARSE_PROMPT,
            user_prompt=prompt,
            temperature=0.2,
            max_tokens=4096,
        )

        return self._parse_json(resp)

    def parse_pdf(self, pdf_path: Path) -> dict:
        """从 PDF 提取文本并解析"""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("请安装 PyMuPDF: pip install PyMuPDF")

        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()

        if not text.strip():
            raise RuntimeError(f"PDF 文件中未提取到文本: {pdf_path}")

        return self.parse_text(text)

    def parse(self, source: str | Path) -> dict:
        """自动识别输入类型并解析"""
        path = Path(source) if isinstance(source, str) else source

        if not isinstance(source, Path):
            source = Path(source)

        if not path.exists():
            # 视为纯文本
            return self.parse_text(str(source))

        if path.suffix.lower() == '.pdf':
            return self.parse_pdf(path)
        else:
            text = path.read_text(encoding="utf-8")
            return self.parse_text(text)

    def save(self, resume: dict, filepath: Path):
        """保存结构化简历"""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(json.dumps(resume, ensure_ascii=False, indent=2), "utf-8")

    def load(self, filepath: Path) -> dict:
        """加载结构化简历"""
        return json.loads(filepath.read_text("utf-8"))

    def get_summary(self, resume: dict) -> str:
        """生成简历摘要文本（用于 prompt 上下文）"""
        parts = []

        if resume.get("name"):
            parts.append(f"姓名：{resume['name']}")

        edu = resume.get("education", {})
        if edu:
            parts.append(f"学历：{edu.get('degree', '')} {edu.get('school', '')} {edu.get('major', '')}")

        parts.append(f"工作年限：{resume.get('years_of_experience', 0)}年")

        skills = resume.get("skills", [])
        if skills:
            parts.append(f"技能：{', '.join(skills[:15])}")

        for exp in resume.get("work_experience", [])[:3]:
            parts.append(f"{exp.get('title', '')} @ {exp.get('company', '')} ({exp.get('duration', '')})")

        if resume.get("desired_role"):
            parts.append(f"期望职位：{resume['desired_role']}")

        return "\n".join(parts)

    @staticmethod
    def _parse_json(resp: str) -> dict:
        m = re.search(r'\{.*\}', resp, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        return {"raw_text": resp, "parse_error": True}
