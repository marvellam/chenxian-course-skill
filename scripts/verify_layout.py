"""Check real generated pixels and copy before delivery; no source writes."""
import argparse
import json
from pathlib import Path

import numpy as np
from bs4 import BeautifulSoup
from PIL import Image
from typography import load_font

ROOT = Path(__file__).resolve().parent.parent
OUTLINE = ROOT / 'output/outline-editable-v1'
PAPER = '#f1ebdf'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_heading(im, top, name):
    # Subtract the empty frame to measure actual glyph pixels, not a line box.
    frame = Image.open(ROOT / 'assets/components/section-heading-frame@2x.png')
    frame = frame.convert('RGBA').resize((456, 80), Image.Resampling.LANCZOS)
    empty = Image.new('RGB', (456, 80), PAPER)
    empty.paste(frame, (0, 0), frame)
    actual = im.convert('RGB').crop((312, round(top), 768, round(top) + 80))
    ys, xs = np.where(np.any(np.asarray(actual) != np.asarray(empty), axis=2))
    require(len(xs) > 0, f'{name}: heading is missing')
    # The inner frame is y=11..69. At least 3px of clear space is required.
    require(xs.min() >= 84 and xs.max() <= 372 and ys.min() >= 14 and ys.max() <= 66,
            f'{name}: heading touches or exceeds the frame')
    require(abs((xs.min() + xs.max()) / 2 - 227.5) <= 3 and
            abs((ys.min() + ys.max()) / 2 - 40) <= 2,
            f'{name}: heading is not centered')
    return {'name': name, 'ink_y': [int(ys.min()), int(ys.max())]}


def verify(export=None):
    for name in ['Regular', 'Medium', 'Bold']:
        family, _ = load_font(f'SourceHanSans-{name}.ttc', 44).getname()
        require(family == 'Source Han Sans SC', f'{name}: expected Simplified Chinese font')
    data = json.loads((OUTLINE / 'content.json').read_text(encoding='utf-8'))
    checks = []
    for platform in ['微信小店版', '小红书版']:
        doc = BeautifulSoup((OUTLINE / f'课程大纲与须知_可编辑母版_{platform}.html')
                            .read_text(encoding='utf-8'), 'html.parser')
        headings = doc.select('h2')
        require([h.get_text() for h in headings] == ['课程大纲', '领取课程', '课程须知'],
                f'{platform}: missing or unexpected framed headings')
        for h in headings:
            require('data-frame-top' in h.attrs, 'Stale output: rebuild the outline first')
            name = h.find_parent('section')['data-screen-label']
            with Image.open(OUTLINE / f'{name}.png') as im:
                require(im.width == 1080, f'{name}: incorrect width')
                checks.append(check_heading(im, float(h['data-frame-top']), platform + '/' + h.get_text()))
        for i, module in enumerate(data['modules'], 1):
            for lesson in module['lessons']:
                key = f'{i}-{lesson["number"]}'
                node = doc.select_one(f'[data-lesson="{key}"]')
                require(node is not None and node.get_text() == lesson['title'], f'{key}: title changed')
                for j, topic in enumerate(lesson.get('topics', []), 1):
                    node = doc.select_one(f'[data-topic="{key}-{j}"]')
                    require(node is not None and node.get_text() == topic, f'{key}-{j}: topic changed')
        if data.get('prologue'):
            for j, topic in enumerate(data['prologue']['topics'], 1):
                node = doc.select_one(f'[data-prologue-topic="{j}"]')
                require(node is not None and node.get_text() == topic, f'Prologue {j}: copy changed')
    if export:
        png = export / '_备份与母版/无损PNG'
        chapters = []
        for i, title in enumerate(['山水篇', '花鸟篇', '人物篇'], 1):
            with Image.open(OUTLINE / f'课程大纲_{i}_{title}.png') as im:
                chapters.append(np.asarray(im).copy())
        with Image.open(png / '06_课程大纲_山水花鸟人物三篇.png') as im:
            require(np.array_equal(np.asarray(im), np.concatenate(chapters, axis=0)),
                    '06: stale or incorrectly merged outline')
        for platform in ['微信小店版', '小红书版']:
            files = sorted((export / platform).glob('*.jpg'))
            require(len(files) == 8 and [p.name[:2] for p in files] == [f'{i:02d}' for i in range(1, 9)],
                    f'{platform}: expected 8 ordered JPGs')
            for path in files:
                with Image.open(path) as jpg, Image.open(png / (path.stem + '.png')) as lossless:
                    require(jpg.width == 1080 and jpg.size == lossless.size, f'{path.name}: size mismatch')
            doc = BeautifulSoup((OUTLINE / f'课程大纲与须知_可编辑母版_{platform}.html')
                                .read_text(encoding='utf-8'), 'html.parser')
            note = next(h for h in doc.select('h2') if h.get_text() == '课程须知')
            cut = round(float(note['data-frame-top']) - 45)
            with Image.open(OUTLINE / f'课程须知与问题_{platform}.png') as tail:
                for name, box in [(f'07_领取课程_{platform}', (0, 0, 1080, cut)),
                                  ('08_课程须知', (0, cut, 1080, tail.height))]:
                    with Image.open(png / f'{name}.png') as im:
                        require(np.array_equal(np.asarray(im), np.asarray(tail.crop(box))),
                                f'{name}: incorrect split or stale export')
        for name, top in [('03_老师介绍', 46), ('04_课程亮点', 0),
                          ('06_课程大纲_山水花鸟人物三篇', 24),
                          ('07_领取课程_微信小店版', 28), ('07_领取课程_小红书版', 28),
                          ('08_课程须知', 45)]:
            with Image.open(png / f'{name}.png') as im:
                checks.append(check_heading(im, top, name))
        archived = export / '_备份与母版/课程大纲_可修改文案.json'
        require(json.loads(archived.read_text(encoding='utf-8')) == data, 'Archived copy differs from source')
    return {'status': 'passed', 'headings': checks, 'export_checked': export is not None}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', type=Path, help='Optional full export directory, relative to package root')
    args = parser.parse_args()
    target = ROOT / args.export if args.export is not None else None
    print(json.dumps(verify(target), ensure_ascii=False, indent=2))
