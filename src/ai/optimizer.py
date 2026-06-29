"""AI 简历优化器 — 优化简历内容并生成可编辑文件"""
import json, re
from pathlib import Path
from datetime import datetime
from .client import DeepSeekClient
from .prompts import RESUME_OPTIMIZE_PROMPT, RESUME_OPTIMIZE_USER


class ResumeOptimizer:
    def __init__(self, client: DeepSeekClient, data_dir: Path = None):
        self.client = client
        self.data_dir = data_dir or Path("data")

    def optimize(self, resume: dict, target_direction: str = "",
                 target_city: str = "", target_salary: str = "",
                 extra_info: str = "") -> dict:
        """AI 优化简历"""
        print("[Optimizer] AI 优化简历中...")

        prompt = RESUME_OPTIMIZE_USER.format(
            resume_json=json.dumps(resume, ensure_ascii=False, indent=2),
            target_direction=target_direction or "AI视频编解码 / Python AI开发 / AIGC内容创作",
            target_city=target_city or "深圳",
            target_salary=target_salary or "15-20K",
            extra_info=extra_info or "GitHub: sanshisanAIGC (novel-factory, bilibili-to-feishu-note-bot 等项目)",
        )

        resp = self.client.chat_with_retry(
            system_prompt=RESUME_OPTIMIZE_PROMPT,
            user_prompt=prompt,
            temperature=0.4,
            max_tokens=4096,
        )

        optimized = self._parse_response(resp)
        print(f"[Optimizer] 优化完成")
        for note in optimized.get("optimization_notes", [])[:3]:
            print(f"  - {note[:80]}")
        return optimized

    def generate_markdown(self, original: dict, optimized: dict) -> str:
        """生成可编辑的 Markdown 简历"""
        md = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        md.append(f"# 个人简历")
        md.append(f"> AI 优化版本 | 生成时间: {now}")
        md.append(f"> 目标方向: {optimized.get('target_position', 'AI视频/AI编程')}")
        md.append("")

        # 个人简介
        summary = optimized.get("summary", "")
        if summary:
            md.append("## 个人简介")
            md.append(summary)
            md.append("")

        # 技能栈
        skills = optimized.get("optimized_skills", {})
        if skills:
            md.append("## 技能栈")
            for level, items in skills.items():
                if items:
                    md.append(f"- **{level}**: {', '.join(items)}")
            md.append("")

        # 工作经历
        md.append("## 工作经历")
        for exp in optimized.get("work_experience", []):
            md.append(f"### {exp.get('title', '')} | {exp.get('company', '')}")
            md.append(f"*{exp.get('duration', '')}*")
            md.append("")
            for h in exp.get("highlights", []):
                md.append(f"- {h}")
            if exp.get("tech_stack"):
                md.append(f"- 技术栈: {', '.join(exp['tech_stack'])}")
            md.append("")

        # 项目经验
        projects = optimized.get("projects", [])
        if projects:
            md.append("## 项目经验")
            for proj in projects:
                md.append(f"### {proj.get('name', '')}")
                if proj.get('role'):
                    md.append(f"*{proj['role']}*")
                if proj.get('url'):
                    md.append(f"链接: {proj['url']}")
                md.append("")
                for h in proj.get("highlights", []):
                    md.append(f"- {h}")
                if proj.get("tech_stack"):
                    md.append(f"- 技术栈: {', '.join(proj['tech_stack'])}")
                md.append("")

        # 教育背景
        edu = optimized.get("education", {})
        if edu:
            md.append("## 教育背景")
            md.append(f"**{edu.get('school', '')}** | {edu.get('degree', '')} | {edu.get('major', '')}")
            for h in edu.get("highlights", []):
                md.append(f"- {h}")
            md.append("")

        # 作品集
        portfolio = optimized.get("portfolio", {})
        if portfolio:
            md.append("## 作品集 & 社区影响力")
            if portfolio.get("github"):
                md.append(f"- GitHub: {portfolio['github']}")
            if portfolio.get("community"):
                md.append(f"- 社区: {portfolio['community']}")
            data = portfolio.get("data", {})
            if data:
                parts = []
                if data.get("followers"):
                    parts.append(f"{data['followers']} 粉丝")
                if data.get("stars"):
                    parts.append(f"{data['stars']} Stars")
                if data.get("views"):
                    parts.append(f"{data['views']} 阅读量")
                if parts:
                    md.append(f"- 数据: {', '.join(parts)}")
            md.append("")

        # 求职意向
        md.append("## 求职意向")
        md.append(f"- 目标岗位: {optimized.get('target_position', '')}")
        md.append(f"- 期望城市: 深圳")
        md.append(f"- 期望薪资: 15-20K")
        md.append(f"- 工作类型: 全职")
        md.append("")

        # 优化说明
        notes = optimized.get("optimization_notes", [])
        if notes:
            md.append("---")
            md.append("## 优化说明（AI自动生成）")
            for note in notes:
                md.append(f"- {note}")

        return "\n".join(md)

    def generate_html(self, optimized: dict) -> str:
        """生成可视化 HTML 简历（可直接打印为 PDF）"""
        skills = optimized.get("optimized_skills", {})
        experiences = optimized.get("work_experience", [])
        projects = optimized.get("projects", [])
        edu = optimized.get("education", {})
        portfolio = optimized.get("portfolio", {})

        # 技能标签 HTML
        def skill_tags(items, color):
            return "".join(f'<span class="skill-tag" style="background:{color}">{s}</span>' for s in (items or []))

        all_proficient = skills.get("精通", [])
        all_skilled = skills.get("熟练", [])
        all_familiar = skills.get("了解", [])
        skill_html = skill_tags(all_proficient, "#1a1a2e") + skill_tags(all_skilled, "#16213e") + skill_tags(all_familiar, "#0f3460")

        # 工作经历 HTML
        exp_html = ""
        for exp in experiences:
            highlights = "".join(f"<li>{h}</li>" for h in exp.get("highlights", []))
            tech = ", ".join(exp.get("tech_stack", []))
            exp_html += f"""
            <div class="exp-item">
                <div class="exp-header">
                    <span class="exp-title">{exp.get('title', '')}</span>
                    <span class="exp-company">| {exp.get('company', '')}</span>
                    <span class="exp-date">{exp.get('duration', '')}</span>
                </div>
                <ul>{highlights}</ul>
                <div class="tech-stack">🔧 {tech}</div>
            </div>"""

        # 项目经验 HTML
        proj_html = ""
        for proj in projects:
            highlights = "".join(f"<li>{h}</li>" for h in proj.get("highlights", []))
            tech = ", ".join(proj.get("tech_stack", []))
            url = proj.get("url", "")
            url_html = f'<a href="{url}" class="proj-link">🔗 {url}</a>' if url else ""
            proj_html += f"""
            <div class="proj-item">
                <div class="proj-header">
                    <span class="proj-name">{proj.get('name', '')}</span>
                    <span class="proj-role">{proj.get('role', '')}</span>
                </div>
                {url_html}
                <ul>{highlights}</ul>
                <div class="tech-stack">🔧 {tech}</div>
            </div>"""

        # 作品集
        port_html = ""
        if portfolio:
            parts = []
            gh = portfolio.get("github", "")
            if gh:
                parts.append(f'<a href="{gh}">GitHub</a>')
            if portfolio.get("community"):
                parts.append(portfolio["community"])
            data = portfolio.get("data", {})
            if data.get("views"):
                parts.append(f'阅读量 {data["views"]:,}')
            if data.get("followers"):
                parts.append(f'粉丝 {data["followers"]}')
            port_html = " | ".join(parts)

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>个人简历 - {optimized.get('target_position', '')}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif; background: #e8ecf1; display: flex; justify-content: center; padding: 30px; }}
.resume {{ width: 800px; background: #fff; box-shadow: 0 4px 24px rgba(0,0,0,0.12); border-radius: 4px; overflow: hidden; }}
.header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: #fff; padding: 36px 40px 28px; }}
.header h1 {{ font-size: 28px; font-weight: 700; letter-spacing: 2px; margin-bottom: 8px; }}
.header .subtitle {{ font-size: 15px; opacity: 0.85; margin-bottom: 12px; }}
.header .contact {{ font-size: 13px; opacity: 0.7; display: flex; gap: 20px; flex-wrap: wrap; }}
.header .contact span {{ white-space: nowrap; }}
.content {{ padding: 32px 40px; }}
.section {{ margin-bottom: 28px; }}
.section-title {{ font-size: 17px; font-weight: 700; color: #1a1a2e; border-left: 3px solid #e94560; padding-left: 10px; margin-bottom: 14px; letter-spacing: 1px; }}
.summary {{ color: #444; line-height: 1.8; font-size: 14px; margin-bottom: 8px; }}
.skill-tag {{ display: inline-block; color: #fff; padding: 3px 10px; border-radius: 3px; font-size: 12px; margin: 0 4px 6px 0; }}
.exp-item, .proj-item {{ margin-bottom: 18px; }}
.exp-header, .proj-header {{ margin-bottom: 6px; }}
.exp-title, .proj-name {{ font-weight: 700; font-size: 15px; color: #1a1a2e; }}
.exp-company {{ color: #e94560; font-size: 14px; margin: 0 8px; }}
.exp-date, .proj-role {{ color: #999; font-size: 13px; float: right; }}
.proj-role {{ float: none; margin-left: 12px; }}
ul {{ padding-left: 20px; margin: 6px 0; }}
li {{ color: #555; font-size: 13px; line-height: 1.7; margin-bottom: 3px; }}
.tech-stack {{ color: #888; font-size: 12px; margin-top: 4px; }}
.proj-link {{ color: #0f3460; font-size: 12px; text-decoration: none; display: inline-block; margin: 2px 0 4px; }}
.edu-item {{ color: #444; font-size: 14px; line-height: 1.8; }}
.portfolio {{ color: #444; font-size: 14px; }}
.portfolio a {{ color: #e94560; text-decoration: none; }}
.job-target {{ background: #f8f9fa; border-radius: 6px; padding: 14px 18px; font-size: 14px; color: #555; display: flex; gap: 24px; flex-wrap: wrap; }}
.job-target strong {{ color: #1a1a2e; }}
@media print {{ body {{ background: #fff; padding: 0; }} .resume {{ box-shadow: none; width: 100%; }} }}
</style>
</head>
<body>
<div class="resume">
<div class="header">
    <h1>{optimized.get('summary', '个人简历')[:30]}</h1>
    <div class="subtitle">{optimized.get('target_position', '')}</div>
    <div class="contact">
        <span>📧 简历由 AI 优化生成</span>
        <span>📍 深圳</span>
        <span>💰 15-20K</span>
    </div>
</div>
<div class="content">
    <div class="section">
        <div class="section-title">个人概述</div>
        <div class="summary">{optimized.get('summary', '')}</div>
    </div>

    <div class="section">
        <div class="section-title">核心技能</div>
        <div>{skill_html}</div>
    </div>

    <div class="section">
        <div class="section-title">工作经历</div>
        {exp_html}
    </div>

    <div class="section">
        <div class="section-title">项目经验</div>
        {proj_html}
    </div>

    <div class="section">
        <div class="section-title">教育背景</div>
        <div class="edu-item">
            <strong>{edu.get('school', '')}</strong> | {edu.get('degree', '')} | {edu.get('major', '')}
            {"".join(f"<br>{h}" for h in edu.get("highlights", []))}
        </div>
    </div>

    <div class="section">
        <div class="section-title">作品集 & 社区</div>
        <div class="portfolio">{port_html}</div>
    </div>

    <div class="section">
        <div class="section-title">求职意向</div>
        <div class="job-target">
            <span><strong>岗位:</strong> {optimized.get('target_position', '')}</span>
            <span><strong>城市:</strong> 深圳</span>
            <span><strong>薪资:</strong> 15-20K</span>
            <span><strong>类型:</strong> 全职</span>
        </div>
    </div>
</div>
</div>
</body>
</html>"""
        return html

    def save_outputs(self, original: dict, optimized: dict):
        """保存优化结果到文件"""
        # 1. 保存优化后的结构化 JSON
        opt_file = self.data_dir / "resume_optimized.json"
        opt_file.write_text(json.dumps({
            "original": original,
            "optimized": optimized,
            "generated_at": datetime.now().isoformat(),
        }, ensure_ascii=False, indent=2), encoding="utf-8")

        # 2. 生成 Markdown（可编辑）
        md_content = self.generate_markdown(original, optimized)
        md_file = self.data_dir / "resume_optimized.md"
        md_file.write_text(md_content, encoding="utf-8")

        # 3. 生成可视化 HTML 简历（可打印 PDF）
        html_content = self.generate_html(optimized)
        html_file = self.data_dir / "resume_optimized.html"
        html_file.write_text(html_content, encoding="utf-8")

        print(f"\n[Optimizer] 文件已生成:")
        print(f"  JSON: {opt_file}")
        print(f"  Markdown: {md_file} (用 Typora/VS Code 打开编辑)")
        print(f"  HTML: {html_file} (浏览器打开可视化简历，Ctrl+P 打印PDF)")
        return opt_file, md_file, html_file

    @staticmethod
    def _parse_response(resp: str) -> dict:
        m = re.search(r'\{.*\}', resp, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        return {"error": "parse_failed", "raw": resp[:500]}
