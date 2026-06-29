"""从编辑后的 Markdown 重建 HTML 简历 + 作品集网站"""
import re, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
md = Path('data/resume_optimized.md').read_text('utf-8')

def get_section(title):
    pattern = rf'## {title}\n(.*?)(?=\n## |\n---|\Z)'
    m = re.search(pattern, md, re.DOTALL)
    return m.group(1).strip() if m else ''

def get_skill_tags():
    skills_section = get_section('技能栈')
    tags = {}
    for line in skills_section.split('\n'):
        m = re.match(r'- \*\*(.+?)\*\*: (.+)', line)
        if m:
            level = m.group(1).strip()
            items = [s.strip() for s in m.group(2).split(',')]
            tags[level] = items
    return tags

def get_work_exp():
    text = get_section('工作经历')
    exps = []
    blocks = re.split(r'\n### ', '\n' + text)
    for block in blocks:
        if not block.strip():
            continue
        lines = block.strip().split('\n')
        header = lines[0].replace('### ', '')
        parts = header.split('|')
        title = parts[0].strip() if parts else ''
        company = parts[1].strip() if len(parts) > 1 else ''
        duration = ''
        highlights = []
        tech = ''
        for line in lines[1:]:
            s = line.strip()
            if s.startswith('*') and not duration:
                duration = s.replace('*', '').strip()
            elif s.startswith('- ') and '技术栈' not in s:
                highlights.append(s[2:].strip())
            elif '技术栈:' in s:
                tech = s.split('技术栈:', 1)[1].strip()
        exps.append({'title': title, 'company': company, 'duration': duration,
                      'highlights': highlights, 'tech': tech})
    return exps

def get_projects():
    text = get_section('项目经验')
    projs = []
    blocks = re.split(r'\n### ', '\n' + text)
    for block in blocks:
        if not block.strip():
            continue
        lines = block.strip().split('\n')
        header = lines[0].replace('### ', '')
        role = ''
        url = ''
        highlights = []
        tech = ''
        for line in lines[1:]:
            s = line.strip()
            if s.startswith('*'):
                role = s.replace('*', '').strip()
            elif s.startswith('链接:'):
                url = s.split('链接:', 1)[1].strip()
            elif s.startswith('- ') and '技术栈' not in s:
                highlights.append(s[2:].strip())
            elif '技术栈:' in s:
                tech = s.split('技术栈:', 1)[1].strip()
        projs.append({'name': header, 'role': role, 'url': url,
                       'highlights': highlights, 'tech': tech})
    return projs

summary = get_section('个人简介')
skills = get_skill_tags()
experiences = get_work_exp()
projects = get_projects()
education_text = get_section('教育背景')
portfolio_text = get_section('作品集')
job_text = get_section('求职意向')

target_match = re.search(r'目标方向[：:]\s*(.+)', md)
target = target_match.group(1).strip() if target_match else 'AIGC内容创作'

def skill_tags(items, color):
    if not items:
        return ''
    return ''.join(f'<span class="skill-tag" style="background:{color}">{s}</span>' for s in items)

all_tags = (skill_tags(skills.get('精通', []), '#1a1a2e') +
            skill_tags(skills.get('熟练', []), '#16213e') +
            skill_tags(skills.get('了解', []), '#0f3460'))

exp_html = ''
for exp in experiences:
    hl = ''.join(f'<li>{h}</li>' for h in exp['highlights'])
    t = f'<div class="tech-stack">🔧 {exp["tech"]}</div>' if exp.get('tech') else ''
    exp_html += f'''
    <div class="exp-item">
        <div class="exp-header">
            <span class="exp-title">{exp["title"]}</span>
            <span class="exp-company">| {exp["company"]}</span>
            <span class="exp-date">{exp["duration"]}</span>
        </div>
        <ul>{hl}</ul>
        {t}
    </div>'''

proj_html = ''
for proj in projects:
    hl = ''.join(f'<li>{h}</li>' for h in proj['highlights'])
    t = f'<div class="tech-stack">🔧 {proj["tech"]}</div>' if proj.get('tech') else ''
    r = f'<span class="proj-role">{proj["role"]}</span>' if proj.get('role') else ''
    proj_html += f'''
    <div class="proj-item">
        <div class="proj-header">
            <span class="proj-name">{proj["name"]}</span>
            {r}
        </div>
        <ul>{hl}</ul>
        {t}
    </div>'''

edu_lines = education_text.split('\n')
edu_first = edu_lines[0].replace('**', '').split('|')
edu_school = edu_first[0].strip() if len(edu_first) > 0 else ''
edu_degree = edu_first[1].strip() if len(edu_first) > 1 else ''
edu_major = edu_first[2].strip() if len(edu_first) > 2 else ''
edu_hl = ''.join(f'<br>{l.strip("- ")}' for l in edu_lines[1:] if l.strip().startswith('-'))

port_parts = []
for l in [x.strip('- ').strip() for x in portfolio_text.split('\n') if x.strip().startswith('-')]:
    # Remove URLs (no links in resume)
    l = re.sub(r'https?://[^\s)]+', '', l).strip()
    if l:
        port_parts.append(l)
port_html = ' | '.join(port_parts)

job_parts = []
for l in [x.strip('- ').strip() for x in job_text.split('\n') if x.strip().startswith('-')]:
    if '：' in l or ':' in l:
        sep = '：' if '：' in l else ':'
        k, v = l.split(sep, 1)
        job_parts.append(f'<span><strong>{k}:</strong> {v}</span>')
    else:
        job_parts.append(f'<span>{l}</span>')
job_target = ''.join(job_parts)

# ━━━━ 简历 HTML ━━━━
resume_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>个人简历 - {target}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Microsoft YaHei', sans-serif; background: #e8ecf1; display: flex; justify-content: center; padding: 30px; }}
.resume {{ width: 800px; background: #fff; box-shadow: 0 4px 24px rgba(0,0,0,0.12); border-radius: 4px; overflow: hidden; }}
.header {{ background: #4a6380; color: #fff; padding: 28px 40px; display: flex; align-items: center; gap: 30px; }}
.header-info {{ flex: 1; }}
.header-info h1 {{ font-size: 24px; font-weight: 700; letter-spacing: 2px; margin-bottom: 4px; }}
.header-info .subtitle {{ font-size: 14px; opacity: 0.85; }}
.photo-placeholder {{ width: 90px; height: 120px; border: 2px dashed rgba(255,255,255,0.6); border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 12px; opacity: 0.6; flex-shrink: 0; }}
.content {{ padding: 32px 40px; }}
.section {{ margin-bottom: 24px; }}
.section-title {{ font-size: 16px; font-weight: 700; color: #1a1a2e; border-left: 3px solid #4a6380; padding-left: 10px; margin-bottom: 12px; }}
.summary {{ color: #444; line-height: 1.8; font-size: 14px; background: #f8f9fa; padding: 14px; border-radius: 6px; }}
.skill-tag {{ display: inline-block; color: #fff; padding: 3px 10px; border-radius: 3px; font-size: 12px; margin: 0 4px 6px 0; }}
.exp-item, .proj-item {{ margin-bottom: 16px; }}
.exp-header {{ margin-bottom: 4px; }}
.exp-title {{ font-weight: 700; font-size: 15px; color: #1a1a2e; }}
.exp-company {{ color: #e94560; font-size: 14px; margin: 0 8px; }}
.exp-date {{ color: #999; font-size: 13px; float: right; }}
ul {{ padding-left: 20px; margin: 4px 0; }}
li {{ color: #555; font-size: 13px; line-height: 1.7; margin-bottom: 2px; }}
.tech-stack {{ color: #888; font-size: 12px; margin-top: 2px; }}
.edu-item {{ color: #444; font-size: 14px; line-height: 1.8; }}
.job-target {{ background: #f8f9fa; border-radius: 6px; padding: 12px 16px; font-size: 14px; color: #555; display: flex; gap: 20px; flex-wrap: wrap; }}
.job-target strong {{ color: #1a1a2e; }}
@media print {{ body {{ background: #fff; padding: 0; }} .resume {{ box-shadow: none; width: 100%; }} }}
</style>
</head>
<body>
<div class="resume">
<div class="header">
    <div class="header-info">
        <h1>{target}</h1>
        <div class="subtitle">AIGC内容创作 · AI科技自媒体 · 深圳 · 15-20K</div>
    </div>
    <div class="photo-placeholder">证件照</div>
</div>
<div class="content">
    <div class="section">
        <div class="section-title">个人概述</div>
        <div class="summary">{summary}</div>
    </div>
    <div class="section">
        <div class="section-title">核心技能</div>
        <div>{all_tags}</div>
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
            <strong>{edu_school}</strong> | {edu_degree} | {edu_major}
            {edu_hl}
        </div>
    </div>
    <div class="section">
        <div class="section-title">作品集 & 社区影响力</div>
        <div class="edu-item">{port_html}</div>
    </div>
    <div class="section">
        <div class="section-title">求职意向</div>
        <div class="job-target">{job_target}</div>
    </div>
</div>
</div>
</body>
</html>'''

Path('data/resume_optimized.html').write_text(resume_html, encoding='utf-8')
print('简历 HTML 已更新: data/resume_optimized.html')
print(f'  - 蓝色区域仅标题，无简介')
print(f'  - 右边预留证件照位置')
print(f'  - 已移除所有链接')

# ━━━━ 作品集网站 (绿色简约风) ━━━━
portfolio_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>叁十三 · AIGC创作者 — 作品集</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Microsoft YaHei', sans-serif; background: #f5f5f0; color: #1a1a1a; line-height: 1.6; }
a { color: #1a1a1a; text-decoration: none; }
a:hover { color: #5a9a5a; }
.hero { background: #f5f5f0; padding: 80px 40px 60px; text-align: center; border-bottom: 1px solid #e0ddd5; }
.hero h1 { font-size: 42px; font-weight: 700; letter-spacing: 3px; color: #1a1a1a; margin-bottom: 12px; }
.hero .tagline { font-size: 18px; color: #333; margin-bottom: 8px; }
.hero p { font-size: 15px; color: #555; max-width: 600px; margin: 12px auto; }
.stats { display: flex; justify-content: center; gap: 48px; margin-top: 36px; flex-wrap: wrap; }
.stat-item { text-align: center; }
.stat-num { font-size: 38px; font-weight: 700; color: #1a1a1a; }
.stat-label { font-size: 13px; color: #666; margin-top: 4px; }
.container { max-width: 1040px; margin: 0 auto; padding: 60px 32px; }
.section-title { font-size: 22px; font-weight: 700; color: #1a1a1a; margin-bottom: 28px; padding-left: 14px; border-left: 3px solid #5a9a5a; letter-spacing: 1px; }
.project-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
.project-card { background: #fff; border-radius: 10px; overflow: hidden; transition: all 0.3s; border: 1px solid #e8e5dd; }
.project-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(90,154,90,0.08); border-color: #a0c8a0; }
.card-body { padding: 22px 24px 16px; }
.card-body h3 { font-size: 17px; color: #1a1a1a; margin-bottom: 6px; }
.card-body .role { font-size: 12px; color: #5a9a5a; margin-bottom: 10px; }
.card-body ul { padding-left: 18px; }
.card-body li { font-size: 13px; color: #333; line-height: 1.7; margin-bottom: 3px; }
.card-body li::marker { color: #5a9a5a; }
.card-tags { padding: 10px 24px; border-top: 1px solid #f0efe8; display: flex; flex-wrap: wrap; gap: 5px; }
.tag { font-size: 11px; padding: 2px 8px; border-radius: 3px; background: #f0efe8; color: #555; }
.skills-section { margin: 60px 0; }
.skill-bar-group { margin-bottom: 18px; }
.skill-bar-label { font-size: 14px; margin-bottom: 5px; color: #1a1a1a; }
.skill-bar-track { background: #e8e5dd; border-radius: 4px; height: 8px; overflow: hidden; }
.skill-bar-fill { height: 100%; border-radius: 4px; background: #5a9a5a; }
.links-section { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-top: 20px; }
.link-card { background: #fff; border: 1px solid #e8e5dd; border-radius: 8px; padding: 18px 22px; display: flex; align-items: center; gap: 14px; transition: all 0.3s; }
.link-card:hover { border-color: #5a9a5a; }
.link-icon { width: 44px; height: 44px; border-radius: 8px; background: #f0efe8; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.link-info .name { font-size: 15px; font-weight: 600; color: #1a1a1a; }
.link-info .desc { font-size: 12px; color: #555; }
.link-info .url { font-size: 11px; color: #5a9a5a; word-break: break-all; }
.timeline { position: relative; padding-left: 28px; border-left: 2px solid #ddd8c8; margin-left: 10px; }
.timeline-item { margin-bottom: 24px; position: relative; }
.timeline-item::before { content: ''; position: absolute; left: -35px; top: 6px; width: 12px; height: 12px; background: #fff; border: 2px solid #5a9a5a; border-radius: 50%; }
.timeline-date { font-size: 12px; color: #5a9a5a; margin-bottom: 2px; }
.timeline-title { font-size: 15px; font-weight: 600; color: #1a1a1a; }
.timeline-sub { font-size: 13px; color: #555; margin-top: 2px; }
.footer { text-align: center; padding: 40px; color: #999; font-size: 13px; border-top: 1px solid #e8e5dd; margin-top: 40px; }
</style>
</head>
<body>

<div class="hero">
    <h1>叁十三 · AIGC创作者</h1>
    <div class="tagline">AI 内容创作 · 模型训练 · 自动化工具开发</div>
    <p>3年AIGC全栈实践，专注AI内容生产自动化与工作流产品化。从模型训练到Agent应用开发，用技术驱动内容规模化增长。</p>
    <div class="stats">
        <div class="stat-item"><div class="stat-num">70+</div><div class="stat-label">ComfyUI工作流</div></div>
        <div class="stat-item"><div class="stat-num">80K+</div><div class="stat-label">Liblib模型使用量</div></div>
        <div class="stat-item"><div class="stat-num">50+</div><div class="stat-label">LoRA模型/作品发布</div></div>
        <div class="stat-item"><div class="stat-num">4</div><div class="stat-label">GitHub开源项目</div></div>
    </div>
</div>

<div class="container">
    <h2 class="section-title">社区与链接</h2>
    <div class="links-section">
        <a href="https://www.liblib.art/userpage/494bc2ddc8844273b05f63827b4dbcc5/publish" target="_blank" class="link-card">
            <div class="link-icon">🎨</div>
            <div class="link-info">
                <div class="name">Liblib · 叁十三</div>
                <div class="desc">LoRA模型创作者 | 50+作品 | 80K+使用量</div>
                <div class="url">liblib.art/userpage/494bc2dd...</div>
            </div>
        </a>
        <a href="https://www.xiaohongshu.com/user/profile/5e73caac00000000010074e6" target="_blank" class="link-card">
            <div class="link-icon">📕</div>
            <div class="link-info">
                <div class="name">小红书 · 叁十三AIGC工作室</div>
                <div class="desc">AI模型/工作流/作品分享 | 1.7K+赞</div>
                <div class="url">xiaohongshu.com/user/profile/5e73ca...</div>
            </div>
        </a>
        <a href="https://github.com/sanshisanAIGC" target="_blank" class="link-card">
            <div class="link-icon">💻</div>
            <div class="link-info">
                <div class="name">GitHub · sanshisanAIGC</div>
                <div class="desc">4个开源项目 | Python全栈</div>
                <div class="url">github.com/sanshisanAIGC</div>
            </div>
        </a>
        <a href="https://b23.tv/PgzNC8Z" target="_blank" class="link-card">
            <div class="link-icon">📺</div>
            <div class="link-info">
                <div class="name">B站 · AI教程创作者</div>
                <div class="desc">50篇教程笔记 | 16万+阅读量</div>
                <div class="url">b23.tv/PgzNC8Z</div>
            </div>
        </a>
    </div>

    <h2 class="section-title">开源项目</h2>
    <div class="project-grid">
        <div class="project-card">
            <div class="card-body">
                <h3>novel-factory</h3>
                <div class="role">独立开发者 | AI长篇小说自动写作系统</div>
                <ul>
                    <li>AI作者/编辑/审校多Agent协作，全自动写作→审校→发布</li>
                    <li>DeepSeek v4 Pro驱动，集成飞书文档API云端同步</li>
                    <li>systemd守护进程7×24运行，单次生成10万字长篇</li>
                </ul>
            </div>
            <div class="card-tags">
                <span class="tag">Python</span><span class="tag">DeepSeek</span><span class="tag">多Agent</span><span class="tag">飞书API</span><span class="tag">systemd</span>
            </div>
        </div>
        <div class="project-card">
            <div class="card-body">
                <h3>bilibili-to-feishu-note-bot</h3>
                <div class="role">独立开发者 | B站视频→AI结构化笔记机器人</div>
                <ul>
                    <li>视频下载→Whisper转录→DeepSeek结构化笔记全流程自动化</li>
                    <li>自动生成带时间戳、关键观点的飞书文档，准确率90%+</li>
                    <li>定时监控UP主更新，累计处理视频500+个</li>
                </ul>
            </div>
            <div class="card-tags">
                <span class="tag">Python</span><span class="tag">Whisper</span><span class="tag">DeepSeek</span><span class="tag">B站API</span><span class="tag">ffmpeg</span>
            </div>
        </div>
        <div class="project-card">
            <div class="card-body">
                <h3>job-hunter</h3>
                <div class="role">独立开发者 | Boss直聘AI自动求职系统</div>
                <ul>
                    <li>AI简历解析+JD深度匹配评分+个性化招呼语自动生成</li>
                    <li>boss-agent-cli集成，支持自动搜索/收藏/投递</li>
                    <li>AI事实核查+飞书实时通知，全流程自动化</li>
                </ul>
            </div>
            <div class="card-tags">
                <span class="tag">Python</span><span class="tag">DeepSeek</span><span class="tag">Playwright</span><span class="tag">Agent</span><span class="tag">飞书</span>
            </div>
        </div>
        <div class="project-card">
            <div class="card-body">
                <h3>hot-article-factory</h3>
                <div class="role">独立开发者 | AI热搜文章自动生产系统</div>
                <ul>
                    <li>微博/抖音热搜实时抓取+AI选题+AI写作+AI事实核查</li>
                    <li>头条风格评论文章生成（800-1500字），每日3篇</li>
                    <li>全链路无人值守，每日成本约¥0.03</li>
                </ul>
            </div>
            <div class="card-tags">
                <span class="tag">Python</span><span class="tag">DeepSeek</span><span class="tag">Playwright</span><span class="tag">数据采集</span><span class="tag">调度</span>
            </div>
        </div>
    </div>

    <div class="skills-section">
        <h2 class="section-title">技能矩阵</h2>
        <div class="skill-bar-group">
            <div class="skill-bar-label">Stable Diffusion / ComfyUI 工作流</div>
            <div class="skill-bar-track"><div class="skill-bar-fill" style="width:95%"></div></div>
        </div>
        <div class="skill-bar-group">
            <div class="skill-bar-label">LoRA 模型训练与调优</div>
            <div class="skill-bar-track"><div class="skill-bar-fill" style="width:90%"></div></div>
        </div>
        <div class="skill-bar-group">
            <div class="skill-bar-label">Python / AI Agent（Claude Code / Codex / Open Claw）</div>
            <div class="skill-bar-track"><div class="skill-bar-fill" style="width:80%"></div></div>
        </div>
        <div class="skill-bar-group">
            <div class="skill-bar-label">飞书 / DeepSeek / B站 API 集成</div>
            <div class="skill-bar-track"><div class="skill-bar-fill" style="width:85%"></div></div>
        </div>
        <div class="skill-bar-group">
            <div class="skill-bar-label">AI视频生成（libtv / tapnow）</div>
            <div class="skill-bar-track"><div class="skill-bar-fill" style="width:78%"></div></div>
        </div>
        <div class="skill-bar-group">
            <div class="skill-bar-label">Photoshop / 剪映 / 后期处理</div>
            <div class="skill-bar-track"><div class="skill-bar-fill" style="width:75%"></div></div>
        </div>
    </div>

    <div style="margin-top: 60px;">
        <h2 class="section-title">工作历程</h2>
        <div class="timeline">
            <div class="timeline-item">
                <div class="timeline-date">2026.03 — 2026.06</div>
                <div class="timeline-title">AI训练师 @ 深圳安达曼科技</div>
                <div class="timeline-sub">模型训练 + Agent工具链探索（Claude Code / Codex / Open Claw），明确AI科技自媒体职业方向</div>
            </div>
            <div class="timeline-item">
                <div class="timeline-date">2023.12 — 2026.01</div>
                <div class="timeline-title">AI训练负责人 @ 草图里（广州）科技</div>
                <div class="timeline-sub">管理10+人团队，搭建70+工作流库，推动研发成果产品化</div>
            </div>
            <div class="timeline-item">
                <div class="timeline-date">2022.12 — 2023.12</div>
                <div class="timeline-title">AIGC技术应用与行业实践</div>
                <div class="timeline-sub">B站AIGC内容创作起步，为2家企业搭建AIGC设计管线</div>
            </div>
        </div>
    </div>
</div>

<div class="footer">
    <p>叁十三 · AIGC创作者 &nbsp;|&nbsp; 深圳 &nbsp;|&nbsp; sanshisanAIGC</p>
</div>

</body>
</html>'''

Path('data/portfolio.html').write_text(portfolio_html, encoding='utf-8')
print('作品集网站已生成: data/portfolio.html')
print(f'  - 4个开源项目卡片')
print(f'  - 社区数据展示')
print(f'  - 技能矩阵可视化')
print(f'  - 工作历程时间线')
