"""Section exports from the approved layout source, not browser screenshots."""
from pathlib import Path
import base64, hashlib, json, re, shutil, mimetypes, argparse
from datetime import date as _date
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageChops
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / 'output/detail-entry-v1/课程入口_可编辑母版.html'

parser = argparse.ArgumentParser()
_today = _date.today().strftime('%Y%m%d')
parser.add_argument('--output', default=f'detail-export-v1-{_today}')
parser.add_argument('--version', default='第一版')
parser.add_argument('--date', default=_date.today().strftime('%Y-%m-%d'))
parser.add_argument('--change-note', default='')
args = parser.parse_args()

OUT = ROOT / 'output' / args.output
OUT.mkdir(exist_ok=True)
PNG = OUT / '_备份与母版/无损PNG'
PNG.mkdir(parents=True, exist_ok=True)

PAPER = '#f1ebdf'; INK = '#304e46'; BODY = '#46534d'

# Font resolution: package fonts/ first, then system fonts
_PACKAGE_FONTS = ROOT / 'fonts'
_SYSTEM_FONTS = Path.home() / 'AppData/Local/Microsoft/Windows/Fonts'

FACES = {
    'sans':         'SourceHanSans-Regular.ttc',
    'medium':       'SourceHanSans-Medium.ttc',
    'serif':        'SourceHanSerifCN-Regular-1.otf',
    'serif-medium': 'SourceHanSerifCN-Medium-6.otf',
    'serif-bold':   'SourceHanSerifCN-Bold-2.otf',
}

def _font_path(name):
    p = _PACKAGE_FONTS / name
    if p.exists():
        return p
    s = _SYSTEM_FONTS / name
    if s.exists():
        return s
    raise FileNotFoundError(
        f"Font '{name}' not found in {_PACKAGE_FONTS} or {_SYSTEM_FONTS}.\n"
        "Install fonts from the fonts/ directory: select all, right-click, 'Install for all users'."
    )

html_text = PAGE.read_text(encoding='utf-8')
soup = BeautifulSoup(html_text, 'html.parser')
records = []; native_lines = []


def font(size, face='sans'):
    return ImageFont.truetype(str(_font_path(FACES[face])), size)

def canvas(h):
    return Image.new('RGB', (1080, round(h)), PAPER)

def advance(text, f, spacing=0):
    return f.getlength(text) + len(text) * spacing

def line(im, text, x, y, size, leading, face='sans', fill=BODY, spacing=0, justify=None):
    f = font(size, face); ascent, descent = f.getmetrics()
    baseline = y + (leading - ascent - descent) / 2 + ascent
    d = ImageDraw.Draw(im)
    if justify is not None and len(text) > 1:
        spacing = (justify - f.getlength(text)) / (len(text) - 1)
    if spacing:
        for c in text:
            d.text((x, baseline), c, font=f, fill=fill, anchor='ls')
            x += f.getlength(c) + spacing
    else:
        d.text((x, baseline), text, font=f, fill=fill, anchor='ls')

def wrap(text, size, width, spacing=0, keep=None):
    f = font(size); result = []
    for part in text.split('\n'):
        rest = part
        while rest:
            n = 1
            while n < len(rest) and advance(rest[:n + 1], f, spacing) <= width: n += 1
            while n > 1 and ((n < len(rest) and rest[n] in '，。、；：！？）》"') or rest[n - 1] in '《（"'): n -= 1
            if keep and keep in rest:
                k = rest.index(keep)
                if k < n < k + len(keep): n = k
            assert n > 0
            result.append(rest[:n]); rest = rest[n:]
    assert ''.join(result) == text.replace('\n', '')
    return result

def para(im, text, x, y, size, width, leading, face='sans', fill=BODY, spacing=0, keep=None, justify=False):
    lines = wrap(text, size, width, spacing, keep)
    for i, t in enumerate(lines):
        line(im, t, x, y + i * leading, size, leading, face, fill, spacing,
             width if justify and i < len(lines) - 1 else None)
    native_lines.append({'text': text, 'lines': lines, 'font_size': size, 'width': width, 'leading': leading})
    return y + len(lines) * leading

def heading(im, text, y):
    frame = Image.open(ROOT / 'assets/components/section-heading-frame@2x.png').convert('RGBA').resize((456, 80), Image.Resampling.LANCZOS)
    im.paste(frame, (312, round(y)), frame)
    f = font(52, 'serif-bold')
    line(im, text, (1080 - f.getlength(text)) / 2, y + 11.5, 52, 52, 'serif-bold', INK)

def save(name, im):
    im.save(PNG / f'{name}.png', optimize=True)
    records.append({'name': name, 'size': list(im.size)})
    return im


# 01
opening = canvas(820)
art = Image.open(ROOT / 'output/detail-entry-v1/assets/ni-zan-entry-visual.png').convert('RGB')
art = ImageOps.fit(art, (1080, 1000), method=Image.Resampling.LANCZOS)
art = ImageChops.multiply(art, Image.new('RGB', art.size, PAPER))
alpha = np.clip((910 - np.arange(1000)) / 240, 0, 1) * .86 * 255
mask = Image.fromarray(np.repeat(alpha[:, None], 1080, axis=1).astype('uint8'))
opening.paste(art, (0, -110), mask)
title = soup.select_one('.course-title')
line(opening, title.contents[0], 74, 108, 84, 109.2, 'serif-medium', INK)
line(opening, title.strong.get_text(), 74, 217.2, 164, 205, 'serif-bold', INK)
for i, t in enumerate(soup.select_one('.quote-band').get_text('\n').split('\n')):
    line(opening, t, 77, 490 + i * 80, 50, 80, 'serif-bold', INK)
save('01_课程题图', opening)

# 02
intro = canvas(2400); y = 0
y = para(intro, soup.select_one('.entry-lead').get_text('\n'), 77, y, 50, 920, 82.5) + 70
question_top = y
for i, p in enumerate(soup.select('.questions p')):
    line(intro, p.get_text(), 120, y, 64, 94.72, 'serif-bold', '#29483f')
    y += 94.72 + (20 if i < 2 else 0)
ImageDraw.Draw(intro).rectangle((77, question_top, 79, y - 1), fill='#b6b9a9')
y += 100
ps = soup.select('.entry-copy p')
y = para(intro, ps[0].get_text(), 77, y, 50, 923, 82.5, spacing=-1.5, keep='理解。') + 56
y = para(intro, ps[1].get_text(), 77, y, 50, 923, 82.5) + 65
y = para(intro, ps[2].get_text('\n'), 77, y, 50, 923, 82.5, 'medium', INK)
save('02_课程简介', intro.crop((0, 0, 1080, round(y + 46))))

# 03
teacher = canvas(1500); heading(teacher, '老师介绍', 46)
card = Image.open((PAGE.parent / soup.select_one('.teacher-generated img')['src']).resolve()).convert('RGB').resize((900, 540), Image.Resampling.LANCZOS)
teacher.paste(card, (90, 158))
y = para(teacher, soup.select_one('.teacher-bio').get_text(), 90, 734, 36, 900, 63, justify=True) + 105
save('03_老师介绍', teacher.crop((0, 0, 1080, round(y))))

# 04 / 05
highlight = Image.open((PAGE.parent / soup.select_one('#course-highlights img')['src']).resolve()).convert('RGB')
high = canvas(80 + 80 + highlight.height + 80); heading(high, '课程亮点', 0); high.paste(highlight, (0, 160))
supplement = soup.select_one('#course-highlights .classroom-pair')
if supplement:
    pair = Image.open((PAGE.parent / supplement['src']).resolve()).convert('RGB')
    pair = pair.resize((1000, round(pair.height * 1000 / pair.width)), Image.Resampling.LANCZOS)
    expanded = canvas(high.height + pair.height - 18)
    expanded.paste(high, (0, 0)); expanded.paste(pair, (40, 160 + highlight.height - 18))
    high = expanded
save('04_课程亮点', high)
benefit = Image.open((PAGE.parent / soup.select_one('#treasure-benefit img')['src']).resolve()).convert('RGB')
benefit_canvas = canvas(benefit.height + 80); benefit_canvas.paste(benefit, (0, 0))
save('05_中华珍宝馆助学权益', benefit_canvas)

# 06
O = ROOT / 'output/outline-editable-v1'
chapters = [Image.open(O / f'课程大纲_{i}_{t}.png').convert('RGB') for i, t in [(1, '山水篇'), (2, '花鸟篇'), (3, '人物篇')]]
merged = canvas(sum(im.height for im in chapters)); my = 0
for im in chapters: merged.paste(im, (0, my)); my += im.height
save('06_课程大纲_山水花鸟人物三篇', merged)

# 07 / 08
footer_versions = {}
for platform in ['微信小店版', '小红书版']:
    doc = BeautifulSoup((O / f'课程大纲与须知_可编辑母版_{platform}.html').read_text(encoding='utf-8'), 'html.parser')
    note = next(h for h in doc.select('h2') if h.get_text() == '课程须知')
    note_top = float(re.search(r'top:([\d.]+)px', note['style'])[1]) - 7
    cut = round(note_top - 45)
    im = Image.open(O / f'课程须知与问题_{platform}.png').convert('RGB')
    claim = im.crop((0, 0, 1080, cut)); notes = im.crop((0, cut, 1080, im.height))
    save(f'07_领取课程_{platform}', claim)
    footer_versions[platform] = (claim, notes)
assert np.array_equal(np.asarray(footer_versions['微信小店版'][1]), np.asarray(footer_versions['小红书版'][1]))
save('08_课程须知', footer_versions['微信小店版'][1])

for platform in footer_versions:
    target = OUT / platform; target.mkdir(exist_ok=True)
    selected = []
    for r in records:
        name = r['name']
        if name.startswith('07_') and not name.endswith(platform): continue
        im = Image.open(PNG / f'{name}.png').convert('RGB')
        im.save(target / f'{name}.jpg', quality=97, subsampling=0, optimize=True)
        selected.append(im)
    full = canvas(sum(im.height for im in selected)); fy = 0
    for im in selected: full.paste(im, (0, fy)); fy += im.height
    full.resize((390, round(full.height * 390 / 1080)), Image.Resampling.LANCZOS).save(
        O / f'拼接检查_{platform}_仅供预览.jpg', quality=94
    )

# Portable HTML archive
def uri(path):
    mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    return f'data:{mime};base64,' + base64.b64encode(path.read_bytes()).decode('ascii')

portable = BeautifulSoup(html_text, 'html.parser')
for img in portable.select('img[src]'):
    img['src'] = uri((PAGE.parent / img['src']).resolve())
for lnk in portable.select('link[rel="stylesheet"]'):
    csspath = (PAGE.parent / lnk['href']).resolve()
    css = csspath.read_text(encoding='utf-8')
    css = re.sub(r'url\(["\']?([^"\')]+)["\']?\)',
                 lambda m: 'url("' + uri((csspath.parent / m[1]).resolve()) + '")', css)
    style = portable.new_tag('style'); style.string = css; lnk.replace_with(style)
archive = OUT / '_备份与母版'
(archive / f'中国美术史_详情页{args.version}_可编辑母版.html').write_text(str(portable), encoding='utf-8')
shutil.copy2(O / 'content.json', archive / '课程大纲_可修改文案.json')
(archive / '排版导出核对.json').write_text(json.dumps({
    'method': ('Native composition from current HTML copy, CSS dimensions and original assets; '
               'not a browser screenshot.'),
    'editable_html_source': str(PAGE),
    'intro_and_bio_linebreaks': native_lines,
    'sections': records,
}, ensure_ascii=False, indent=2), encoding='utf-8')

readme = f'''# 中国美术史详情页｜{args.version}（{args.date}）

微信小店版、小红书版各8张，按01至08顺序上传。两版仅第07张领取课程的流程不同；08课程须知相同。06课程大纲已将山水、花鸟、人物三个篇章合为一张，请勿拆成三份。

所有上架JPG宽1080px，保留现有字体与模块比例，使用高质量无色度抽样压缩。拼接检查图仅供浏览，不是上架图。无损PNG及可编辑母版在"_备份与母版"内。

母版已内嵌全部配图；课程简介、大纲、补充简介等原有活字仍可修改。生成图片内部的字保持图片形式。打开HTML需安装思源宋体、思源黑体；上架JPG不依赖字体。修改课程大纲的JSON后需重新导出，已导出的图片不会自动更新。

本次图片从当前制作源排版导出，非浏览器截图。
'''
if supplement:
    readme += '\n第四条课程亮点下的两张课堂配图为等宽等高、上下对齐的已确认版本。\n'
if args.change_note:
    readme += '\n本次更新：' + args.change_note + '\n'
(OUT / '上传顺序与版本说明.md').write_text(readme, encoding='utf-8')

manifest = []
for fp in sorted(OUT.rglob('*')):
    if fp.is_file() and fp.name != '交付校验清单.json':
        manifest.append({
            'file': str(fp.relative_to(OUT)),
            'bytes': fp.stat().st_size,
            'sha256': hashlib.sha256(fp.read_bytes()).hexdigest(),
        })
(OUT / '交付校验清单.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'output': str(OUT), 'sections': records, 'upload_files_each_platform': 8}, ensure_ascii=False))
