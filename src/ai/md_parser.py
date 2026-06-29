"""Markdown 简历解析器 — 从编辑后的 MD 提取结构化数据"""
import re, json
from pathlib import Path


def parse_md_resume(md_text: str, original_optimized: dict) -> dict:
    """从 Markdown 简历中解析更新后的结构化数据"""
    result = original_optimized.copy()

    # 解析目标方向
    m = re.search(r'目标方向[：:]\s*(.+)', md_text)
    if m:
        result["target_position"] = m.group(1).strip()

    # 解析个人简介
    m = re.search(r'## 个人简介\n(.+?)(?=\n##|\Z)', md_text, re.DOTALL)
    if m:
        result["summary"] = m.group(1).strip()

    # 解析技能栈
    skills = {"精通": [], "熟练": [], "了解": []}
    section = re.search(r'## 技能栈\n(.*?)(?=\n##|\Z)', md_text, re.DOTALL)
    if section:
        for line in section.group(1).split('\n'):
            for level, key in [("精通", "精通"), ("熟练", "熟练"), ("了解", "了解")]:
                if key in line:
                    items = re.findall(r'[^,，]+', line.split(':', 1)[-1].replace('**', ''))
                    skills[level] = [s.strip() for s in items if s.strip()]
        result["optimized_skills"] = skills

    # 解析工作经历
    experiences = []
    exp_sections = re.split(r'### (.+?) \| (.+)', md_text)
    # Simple approach: find ### blocks
    exp_blocks = re.findall(
        r'### (.+?)\n\*(.+?)\*\n\n((?:- .+\n?)+)(?:- 技术栈: (.+))?',
        md_text
    )
    for title, duration, highlights_block, tech in exp_blocks:
        highlights = re.findall(r'- (.+)', highlights_block)
        company_match = re.search(r'\| (.+)$', title)
        company = company_match.group(1).strip() if company_match else ""
        role = title.split('|')[0].strip()

        experiences.append({
            "title": role,
            "company": company,
            "duration": duration.strip(),
            "highlights": highlights,
            "tech_stack": [t.strip() for t in tech.split(',')] if tech else []
        })
    if experiences:
        result["work_experience"] = experiences

    # 解析项目经验
    projects = []
    proj_blocks = re.findall(
        r'### (.+?)(?:：(.+?))?\n(?:\*(.+?)\n)?(?:链接: (.+?)\n)?\n((?:- .+\n?)+)(?:- 技术栈: (.+))?',
        md_text
    )
    for name, role, _, url, highlights_block, tech in proj_blocks:
        highlights = re.findall(r'- (.+)', highlights_block)
        projects.append({
            "name": name.strip(),
            "role": role.strip() if role else "独立开发者",
            "url": url.strip() if url else "",
            "highlights": highlights,
            "tech_stack": [t.strip() for t in tech.split(',')] if tech else []
        })
    if projects:
        result["projects"] = projects

    # 解析教育背景
    edu_match = re.search(r'\*\*(.+?)\*\* \| (.+?) \| (.+)', md_text)
    if edu_match:
        result["education"] = {
            "school": edu_match.group(1).strip(),
            "degree": edu_match.group(2).strip(),
            "major": edu_match.group(3).strip(),
            "highlights": []
        }
        # Check for additional education highlights
        edu_section = re.search(r'## 教育背景\n(.*?)(?=\n##|\Z)', md_text, re.DOTALL)
        if edu_section:
            edu_lines = [l.strip('- ').strip() for l in edu_section.group(1).split('\n') if l.startswith('-')]
            result["education"]["highlights"] = edu_lines

    # 解析作品集
    portfolio = {"github": "", "community": "", "data": {}}
    port_section = re.search(r'## 作品集.*?\n(.*?)(?=\n##|\Z)', md_text, re.DOTALL)
    if port_section:
        for line in port_section.group(1).split('\n'):
            line = line.strip('- *').strip()
            if 'github' in line.lower():
                portfolio["github"] = re.findall(r'https?://[^\s)]+', line)[0] if 'http' in line else line
            elif '社区' in line:
                portfolio["community"] = line.split(':', 1)[-1].strip()
            elif '数据' in line:
                nums = re.findall(r'[\d,]+[万kw]?', line)
                if nums:
                    portfolio["data"] = {"views": line}
    result["portfolio"] = portfolio

    return result
