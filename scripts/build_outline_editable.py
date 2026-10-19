"""Build live-text HTML plus static proofs from the editable outline JSON.
Proofs are Pillow composition checks, not browser screenshots.
"""
from pathlib import Path
import json, re, html, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from typography import (load_font, line_baseline, HEADING_FONT, HEADING_SIZE,
                        HEADING_LEADING, HEADING_OFFSET)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'output/outline-editable-v1'
ASSETS = OUT / 'assets'
DATA = json.loads((OUT / 'content.json').read_text(encoding='utf-8'))

PAPER = '#f1ebdf'; INK = '#304e46'; BODY = '#46534d'; MUTED = '#69766b'; LINE = '#b6b9a9'
FACES = {
    'sans':   'SourceHanSans-Regular.ttc',
    'medium': 'SourceHanSans-Medium.ttc',
    'bold':   'SourceHanSans-Bold.ttc',
    'serif':  'SourceHanSerifCN-Heavy-4.otf',
    'heading': HEADING_FONT,
}
CSS_FACES = {
    'bold':   '"Source Han Sans SC","Source Han Sans CN",sans-serif',
    'sans':   '"Source Han Sans SC","Source Han Sans CN",sans-serif',
    'medium': '"Source Han Sans SC","Source Han Sans CN",sans-serif',
    'serif':  '"Source Han Serif CN",serif',
    'heading': '"Source Han Serif CN",serif',
}

def font(size, face='sans'):
    return load_font(FACES[face], size)

def esc(text):
    return html.escape(text, quote=True)

def wrap(text, size, width, face='sans'):
    f = font(size, face); lines = []
    while text:
        n = 1
        while n < len(text) and f.getlength(text[:n + 1]) <= width: n += 1
        while n > 1 and ((n < len(text) and text[n] in '，。、；：！？）》"') or text[n - 1] in '《（"'): n -= 1
        if 0 < len(text) - n <= 2: n -= 2
        lines.append(text[:n]); text = text[n:]
    assert all(f.getlength(s) <= width for s in lines)
    return lines

# Source paintings remain intact inside reusable vector clipping frames.
from prepare_outline_elements import build as build_elements
build_elements()
specs = [('landscape',), ('flower',), ('figure',)]


class Panel:
    def __init__(self):
        self.im = Image.new('RGB', (1080, 7000), PAPER)
        self.d = ImageDraw.Draw(self.im); self.parts = []; self.bottom = 0; self.texts = []

    def text(self, text, x, y, size=44, width=900, face='sans', color=BODY,
             leading=None, align='left', lines=None, tag='p', extra=''):
        lines = lines if lines is not None else wrap(text, size, width, face)
        assert ''.join(lines) == text
        leading = leading or round(size * 1.45)
        f = font(size, face)
        for i, s in enumerate(lines):
            assert f.getlength(s) <= width, (s, width, size)
            xx = x + (width - f.getlength(s)) / 2 if align == 'center' else x
            if face == 'heading':
                baseline = line_baseline(f, y + i * leading, leading)
                self.d.text((xx, baseline), s, font=f, fill=color, anchor='ls')
            else:
                self.d.text((xx, y + i * leading), s, font=f, fill=color, anchor='lt')
        height = len(lines) * leading
        weight = 900 if face == 'serif' else 700 if face in ('bold', 'heading') else 500 if face == 'medium' else 400
        style = (f'left:{x}px;top:{y}px;width:{width}px;font-family:{CSS_FACES[face]};'
                 f'font-size:{size}px;font-weight:{weight};line-height:{leading}px;'
                 f'color:{color};text-align:{align};')
        spans = ''.join(f'<span style="display:block;white-space:pre;">{esc(s)}</span>' for s in lines)
        self.parts.append(f'<{tag} class="editable-copy" style="{esc(style)}" {extra}>{spans}</{tag}>')
        self.texts.append(text); self.bottom = max(self.bottom, y + height)
        return y + height

    def image(self, name, x, y, w, h):
        im = Image.open(ASSETS / name).convert('RGBA').resize((w, h), Image.Resampling.LANCZOS)
        self.im.paste(im, (x, y), im)
        asset_name = name.replace('-header.png', '-header.svg')
        self.parts.append(
            f'<img class="outline-decoration" src="assets/{asset_name}" alt="" aria-hidden="true" '
            f'style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;">'
        )
        self.bottom = max(self.bottom, y + h)

    def line(self, y, x=90, w=900):
        self.d.line((x, y, x + w, y), fill=LINE, width=1)
        self.parts.append(
            f'<div aria-hidden="true" style="position:absolute;left:{x}px;top:{y}px;'
            f'width:{w}px;border-top:1px solid {LINE};"></div>'
        )

    def bullet(self, text_x, y, size, leading):
        cx = text_x - 22; cy = y + size / 2; radius = 4
        self.d.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=INK)
        self.parts.append(
            f'<span class="outline-bullet" aria-hidden="true" style="position:absolute;'
            f'left:{cx - radius}px;top:{y + leading / 2 - radius}px;width:8px;height:8px;'
            f'border-radius:50%;background:{INK};"></span>'
        )

    def label(self, text, x, y):
        self.d.rounded_rectangle((x, y, x + 108, y + 62), radius=7, fill=INK)
        self.parts.append(
            f'<div aria-hidden="true" style="position:absolute;left:{x}px;top:{y}px;'
            f'width:108px;height:62px;background:{INK};border-radius:7px;"></div>'
        )
        self.text(text, x, y + 10, 38, 108, 'medium', PAPER, 50, 'center')

    def heading(self, text, y):
        self.image('section-heading-frame@2x.png', 312, y, 456, 80)
        self.text(text, 312, y + HEADING_OFFSET, HEADING_SIZE, 456, 'heading',
                  INK, HEADING_LEADING, 'center', tag='h2',
                  extra=f'data-frame-top="{y}"')
        return y + 80

    def finish(self, name, tail=60):
        from datetime import date
        height = int(self.bottom + tail)
        self.im = self.im.crop((0, 0, 1080, height))
        self.im.save(OUT / f'{name}.png')
        self.im.resize((390, round(height * 390 / 1080)), Image.Resampling.LANCZOS).save(
            OUT / f'{name}_390宽预览.png'
        )
        return (
            f'<section class="outline-panel" data-screen-label="{esc(name)}" style="height:{height}px;">'
            + ''.join(self.parts) + '</section>',
            height,
        )


panels = []; outlines = []; metrics = []
for idx, module in enumerate(DATA['modules']):
    p = Panel(); y = 24
    if idx == 0:
        y = p.heading('课程大纲', y) + 42
        notice_lines = ['课程更新中，大纲仅供参考，', '以最终上线题目为准']
        y = p.text(DATA['notice'], 90, y, 40, 900, 'sans', MUTED, 60, 'center', lines=notice_lines) + 54
        if DATA.get('prologue'):
            prologue = DATA['prologue']
            p.text(prologue['label'], 90, y + 2, 44, 136, 'bold', INK, 68,
                   extra='data-prologue="label"')
            for topic_idx, topic in enumerate(prologue['topics']):
                p.bullet(242, y, 48, 68)
                y = p.text(topic, 242, y, 48, 748, 'bold', INK, 68,
                           extra=f'data-prologue-topic="{topic_idx + 1}"') + 10
            y += 14
            p.line(y)
            y += 40
    prefix, title = re.split(r'\s+', module['heading'], maxsplit=1)
    p.image(specs[idx][0] + '-header.png', 90, y, 900, 260)
    p.text(title, 112, y + 106, 68, 370, 'serif', INK, 88, tag='h3')
    y += 260; p.line(y)
    for lesson in module['lessons']:
        y += 24
        top = y
        p.text(f"第{lesson['number']}讲", 90, y + 2, 40, 136, 'medium', INK, 64)
        topics = lesson.get('topics', [])
        y = p.text(lesson['title'], 242, y, 44, 748,
                   'bold' if topics else 'sans', INK if topics else BODY, 64,
                   extra=f'data-lesson="{idx + 1}-{lesson["number"]}"')
        if topics:
            y += 16
            for topic_idx, topic in enumerate(topics):
                p.bullet(274, y, 42, 62)
                y = p.text(topic, 274, y, 42, 716, 'sans', BODY, 62,
                           extra=f'data-topic="{idx + 1}-{lesson["number"]}-{topic_idx + 1}"') + 10
        y += 24
        p.line(y)
        metrics.append({
            'module': idx + 1, 'number': lesson['number'],
            'title': lesson['title'], 'topics': topics,
            'top': top, 'row_height': y - top, 'font_size': 44,
        })
    name = f'课程大纲_{idx + 1}_{title}'
    fragment, height = p.finish(name, 140 if idx == 2 else 70)
    outlines.append(fragment); panels.append((name, p.im))


def footer(platform):
    p = Panel(); y = p.heading('领取课程', 28) + 62
    for i, group in enumerate(DATA['claim'][platform]):
        if i:
            y = p.text('↓', 90, y + 4, 38, 900, 'sans', MUTED, 50, 'center') + 10
        for text in group:
            y = p.text(text, 90, y, 44, 900, 'medium', INK, 64, 'center') + 6
    y += 30
    y = p.text(DATA['claim_tip'], 100, y, 38, 880, 'bold', INK, 58, 'center') + 75
    y = p.heading('课程须知', y) + 48
    for label, text in DATA['purchase_notes']:
        p.label(label, 90, y + 4)
        y = p.text(text, 226, y, 44, 764, 'sans', BODY, 66) + 34
    p.bottom = y
    name = '课程须知与问题_' + ('微信小店版' if platform == 'wechat' else '小红书版')
    fragment, height = p.finish(name, 40)
    return fragment, p.im, name


wechat, wechat_im, wechat_name = footer('wechat')
xhs, xhs_im, xhs_name = footer('xiaohongshu')
panels.append((wechat_name, wechat_im))

css = '''
.outline-live { width:1080px; margin:0; background:#f1ebdf; }
.outline-panel { width:1080px; position:relative; overflow:hidden; background:#f1ebdf; }
.outline-live .editable-copy { position:absolute; margin:0; padding:0; border:0; letter-spacing:0; }
.outline-live .outline-decoration { position:absolute; display:block; }
'''
(OUT / 'outline.css').write_text(css, encoding='utf-8')


def document(body, title):
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{title}</title>'
        '<link rel="stylesheet" href="outline.css">'
        '<style>html{background:#dedfda}body{margin:0}main{margin:0 auto!important}</style>'
        '</head><body><main class="outline-live">' + body + '</main></body></html>'
    )


for platform, tail in [('微信小店版', wechat), ('小红书版', xhs)]:
    (OUT / f'课程大纲与须知_可编辑母版_{platform}.html').write_text(
        document(''.join(outlines) + tail, '中国美术史｜课程大纲与须知'),
        encoding='utf-8',
    )

# Update the main page HTML with the current outline live section.
page = ROOT / 'output/detail-entry-v1/课程入口_可编辑母版.html'
backup = OUT / '添加课程大纲前_详情页备份.html'
if not backup.exists():
    shutil.copy2(page, backup)
source = page.read_text(encoding='utf-8')
if '.outline-live {' not in source:
    source = source.replace('  </style>', css + '  </style>', 1)
body = (''.join(outlines) + wechat).replace('src="assets/', 'src="../outline-editable-v1/assets/')
section = ('<section class="outline-live" id="course-outline-live" aria-label="课程大纲与须知">'
           + body + '</section>')
if 'id="course-outline-live"' in source:
    start = source.index('<section class="outline-live" id="course-outline-live"')
    end = source.index('  </main>', start)
    source = source[:start] + section + '\n' + source[end:]
else:
    source = source.replace('  </main>', section + '\n  </main>', 1)
page.write_text(source, encoding='utf-8')

# Merged proof: all three chapters in reading order.
from datetime import date
merged_name = f'课程大纲_三篇合并_{date.today().strftime("%Y%m%d")}'
all_chapters = [im for name, im in panels if name.startswith('课程大纲_')]
merged = Image.new('RGB', (1080, sum(im.height for im in all_chapters)), PAPER)
my = 0
for im in all_chapters:
    merged.paste(im, (0, my)); my += im.height
merged.save(OUT / f'{merged_name}.png')

# Inspection sheet and reading proof.
thumbs = []
for name, im in panels:
    thumbs.append(im.resize((390, round(im.height * 390 / 1080)), Image.Resampling.LANCZOS))
sheet = Image.new('RGB', (390 * 4 + 24 * 3, max(t.height for t in thumbs)), PAPER)
for i, im in enumerate(thumbs):
    sheet.paste(im, (i * 414, 0))
sheet.save(OUT / '课程大纲与须知_并排检查.png')
full = Image.new('RGB', (1080, sum(im.height for _, im in panels)), PAPER)
y = 0
for _, im in panels:
    full.paste(im, (0, y)); y += im.height
full.save(OUT / '课程大纲与须知_整段预览.png')

manifest = {
    'source_revision': DATA['source_revision'],
    'outline_source': DATA.get('outline_source'),
    'prologue': DATA.get('prologue'),
    'lecture_count': len(metrics),
    'counts': [len(m['lessons']) for m in DATA['modules']],
    'lesson_font': 44, 'show_faq': False, 'show_chapter_prefix': False,
    'claim_tip_weight': 700,
    'artwork_treatment': 'original artwork with vector contour clipping and thin outline',
    'notes': ('Plain editable HTML text with independent image assets; '
              'PNG files are static composition proofs, not browser screenshots.'),
    'main_page_platform': 'wechat',
    'metrics': metrics,
    'panels': [{'name': name, 'size': list(im.size)} for name, im in panels],
}
(OUT / 'production.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
print(json.dumps({
    'lectures': len(metrics),
    'panel_heights': [im.height for _, im in panels],
    'main_page_appended': True,
    'merged_proof': merged_name + '.png',
}, ensure_ascii=False))
