"""从 Markdown 简历生成可编辑 Word 文档 — 公文标准字体"""
import re, sys, io
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
md_text = Path('data/resume_optimized.md').read_text('utf-8')

# Colors
GREEN     = RGBColor(0x5a, 0x9a, 0x5a)
GREEN_DARK = RGBColor(0x3d, 0x7a, 0x3d)
BLACK     = RGBColor(0x1a, 0x1a, 0x1a)
GRAY      = RGBColor(0x55, 0x55, 0x55)
LGRAY     = RGBColor(0x88, 0x88, 0x88)
WHITE     = RGBColor(0xff, 0xff, 0xff)

FONT_TITLE = '黑体'   # 黑体
FONT_BODY  = '仿宋'    # 仿宋

def get_section(title):
    pattern = rf'## {title}\n(.*?)(?=\n## |\n---|\Z)'
    m = re.search(pattern, md_text, re.DOTALL)
    return m.group(1).strip() if m else ''

def set_font(run, name, size, bold=False, color=BLACK):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.insert(0, rFonts)
    rFonts.set(qn('w:eastAsia'), name)

def add_green_header(doc):
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else OxmlElement('w:tblPr')
    tblW = OxmlElement('w:tblW')
    tblW.set(qn('w:w'), '5000')
    tblW.set(qn('w:type'), 'pct')
    tblPr.append(tblW)

    left = table.cell(0, 0)
    left.width = Cm(12)
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), '5a9a5a')
    shading.set(qn('w:val'), 'clear')
    left._tc.get_or_add_tcPr().append(shading)
    left.paragraphs[0].clear()

    target_match = re.search(r'目标方向[：:]\s*(.+)', md_text)
    target = target_match.group(1).strip() if target_match else 'AIGC内容创作者'

    p = left.paragraphs[0]
    p.paragraph_format.space_before = Pt(20)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.left_indent = Cm(1.2)
    run = p.add_run(target)
    set_font(run, FONT_TITLE, 22, bold=True, color=WHITE)

    p2 = left.add_paragraph()
    p2.paragraph_format.space_before = Pt(2)
    p2.paragraph_format.space_after = Pt(0)
    p2.paragraph_format.left_indent = Cm(1.2)
    run2 = p2.add_run('AIGC内容创作 · AI科技自媒体 · 深圳 · 15-20K')
    set_font(run2, FONT_BODY, 11, color=WHITE)

    right = table.cell(0, 1)
    right.width = Cm(6)
    shading2 = OxmlElement('w:shd')
    shading2.set(qn('w:fill'), '3d7a3d')
    shading2.set(qn('w:val'), 'clear')
    right._tc.get_or_add_tcPr().append(shading2)
    right.paragraphs[0].clear()
    pr = right.paragraphs[0]
    pr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pr.paragraph_format.space_before = Pt(14)
    run_pr = pr.add_run('证件照')
    run_pr.font.size = Pt(10)
    run_pr.font.color.rgb = WHITE

    doc.add_paragraph()

def add_section_title(doc, title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(8)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    left_border = OxmlElement('w:left')
    left_border.set(qn('w:val'), 'single')
    left_border.set(qn('w:sz'), '12')
    left_border.set(qn('w:space'), '6')
    left_border.set(qn('w:color'), '5a9a5a')
    pBdr.append(left_border)
    pPr.append(pBdr)
    run = p.add_run(title)
    set_font(run, FONT_TITLE, 15, bold=True)
    return p

def add_para(doc, text, size=12, bold=False, color=BLACK, font=None, spacing_after=4):
    if font is None:
        font = FONT_BODY
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(spacing_after)
    p.paragraph_format.line_spacing = 1.5
    run = p.add_run(text)
    set_font(run, font, size, bold, color)
    return p

def add_bullet(doc, text, size=12):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.left_indent = Cm(0.8)
    p.paragraph_format.first_line_indent = Cm(-0.4)
    p.paragraph_format.line_spacing = 1.5
    run = p.add_run('• ' + text)
    set_font(run, FONT_BODY, size, color=BLACK)
    return p

# ━━━━ Build Document ━━━━
doc = Document()

section = doc.sections[0]
section.page_width = Cm(21.0)
section.page_height = Cm(29.7)
section.top_margin = Cm(1.0)
section.bottom_margin = Cm(1.0)
section.left_margin = Cm(1.5)
section.right_margin = Cm(1.5)

style = doc.styles['Normal']
style.font.name = FONT_BODY
style.font.size = Pt(12)
style.element.rPr.rFonts.set(qn('w:eastAsia'), FONT_BODY)
style.paragraph_format.space_after = Pt(6)
style.paragraph_format.line_spacing = 1.5

add_green_header(doc)

# Summary
add_section_title(doc, '个人概述')
add_para(doc, get_section('个人简介'), size=12)

# Skills
add_section_title(doc, '核心技能')
for line in get_section('技能栈').split('\n'):
    m = re.match(r'- \*\*(.+?)\*\*: (.+)', line)
    if m:
        level = m.group(1)
        items = m.group(2)
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        run_l = p.add_run(f'{level}: ')
        set_font(run_l, FONT_TITLE, 12, bold=True)
        run_i = p.add_run(items)
        set_font(run_i, FONT_BODY, 12)

# Work Experience
add_section_title(doc, '工作经历')
for block in re.split(r'\n### ', '\n' + get_section('工作经历')):
    if not block.strip():
        continue
    lines = block.strip().split('\n')
    h = lines[0].replace('### ', '')
    dur = ''
    for l in lines[1:]:
        s = l.strip()
        if s.startswith('*'):
            dur = s.replace('*', '').strip()
            break
    add_para(doc, h, size=13, bold=True, spacing_after=2)
    if dur:
        add_para(doc, dur, size=10, color=GREEN, spacing_after=4)
    for l in lines[1:]:
        s = l.strip()
        if s.startswith('- ') and '技术栈' not in s:
            add_bullet(doc, s[2:], size=12)
    add_para(doc, '', size=4, spacing_after=2)

# Projects
add_section_title(doc, '项目经验')
for block in re.split(r'\n### ', '\n' + get_section('项目经验')):
    if not block.strip():
        continue
    lines = block.strip().split('\n')
    name = lines[0].replace('### ', '')
    role = ''
    for l in lines[1:]:
        s = l.strip()
        if s.startswith('*'):
            role = s.replace('*', '').strip()
            break
    header = name
    if role:
        header += f'  —  {role}'
    add_para(doc, header, size=13, bold=True, spacing_after=4)
    for l in lines[1:]:
        s = l.strip()
        if s.startswith('- ') and '技术栈' not in s:
            add_bullet(doc, s[2:], size=12)
    add_para(doc, '', size=4, spacing_after=2)

# Education
add_section_title(doc, '教育背景')
edu_text = get_section('教育背景')
edu_lines = edu_text.split('\n')
parts = edu_lines[0].replace('**', '').split('|')
edu_school = parts[0].strip() if len(parts) > 0 else ''
edu_degree = parts[1].strip() if len(parts) > 1 else ''
edu_major = parts[2].strip() if len(parts) > 2 else ''
add_para(doc, f'{edu_school}  |  {edu_degree}  |  {edu_major}', size=12, bold=True)
for l in edu_lines[1:]:
    if l.strip().startswith('-'):
        add_bullet(doc, l.strip('- ').strip(), size=12)

# Portfolio
add_section_title(doc, '作品集 & 社区影响力')
for l in get_section('作品集').split('\n'):
    if l.strip().startswith('-'):
        text = re.sub(r'https?://[^\s)]+', '', l.strip('- ')).strip()
        if text:
            add_para(doc, text, size=12, spacing_after=2)

# Job Target
add_section_title(doc, '求职意向')
for l in get_section('求职意向').split('\n'):
    s = l.strip('- ').strip()
    if s:
        add_para(doc, s, size=12, spacing_after=2)

# Footer
add_para(doc, '', size=4, spacing_after=8)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('叁十三 · AIGC创作者  |  深圳  |  sanshisanAIGC')
set_font(run, FONT_BODY, 9, color=LGRAY)

output = Path('data/resume_gw.docx')
doc.save(str(output))
print(f'Word 简历已生成: {output}')
print(f'A4 尺寸 | 黑体标题 + 仿宋正文 | 公文标准字体')
