"""Original artwork in reusable vector clipping frames; no repainting or color changes."""
from pathlib import Path
import json
from xml.sax.saxutils import escape
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import fitz

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'output/outline-editable-v1'
ASSETS = OUT / 'assets'

_PACKAGE_FONTS = ROOT / 'fonts'
_SYSTEM_FONTS = Path.home() / 'AppData/Local/Microsoft/Windows/Fonts'

SPECS = [
 ('landscape', 'mountain', [(79,259),(89,245),(101,239),(106,225),(121,216),(137,205),(152,196),(164,195),(174,184),(190,181),(205,170),(228,168),(243,158),(265,157),(285,164),(304,177),(323,191),(337,211),(351,225),(367,242),(377,252),(390,269),(410,284),(427,299),(408,303),(389,303),(374,301),(360,309),(343,309),(330,321),(309,325),(289,333),(270,330),(256,341),(233,350),(212,349),(196,357),(183,352),(167,354),(155,350),(147,354),(134,343),(120,345),(114,332),(101,326),(100,315),(87,304),(82,283)], 330, 218),
 ('flower', 'flower', [(442,208),(449,221),(480,243),(494,260),(514,246),(534,228),(542,218),(550,232),(582,258),(610,285),(627,267),(653,247),(674,226),(685,270),(693,316),(695,360),(691,392),(711,378),(743,363),(777,353),(816,351),(850,350),(843,388),(828,430),(810,462),(831,465),(850,475),(871,493),(890,506),(911,515),(887,531),(857,554),(827,579),(788,603),(808,614),(825,628),(839,644),(802,649),(764,659),(741,657),(752,682),(760,710),(761,738),(769,760),(734,759),(695,756),(653,749),(618,733),(597,713),(581,685),(571,654),(566,617),(568,595),(552,594),(534,593),(533,626),(522,657),(508,680),(485,701),(454,714),(419,720),(395,722),(392,697),(394,674),(407,650),(377,660),(340,670),(298,680),(260,689),(226,698),(229,676),(224,651),(229,626),(244,605),(269,589),(300,579),(340,575),(381,575),(422,579),(459,584),(425,563),(390,560),(356,554),(321,545),(290,534),(265,515),(245,491),(230,461),(218,427),(209,395),(197,365),(209,368),(225,360),(229,349),(263,350),(298,350),(323,357),(348,365),(350,333),(361,303),(379,274),(401,248),(425,224)], 308, 238),
 ('figure', 'figure', [(158,36),(175,37),(194,42),(207,53),(214,70),(213,87),(207,104),(195,115),(199,123),(213,141),(216,165),(217,191),(215,211),(219,235),(219,258),(216,282),(211,305),(213,326),(222,350),(230,375),(222,380),(213,370),(207,350),(207,377),(219,393),(229,407),(220,421),(202,427),(183,429),(165,422),(146,426),(128,427),(115,433),(97,427),(82,416),(62,402),(49,389),(43,375),(34,354),(28,334),(27,311),(26,289),(29,269),(29,246),(35,221),(39,199),(40,175),(45,151),(49,125),(57,103),(65,87),(77,77),(91,72),(105,77),(115,85),(122,88),(117,76),(115,65),(124,56),(132,51),(142,44)], 210, 242),
]


def build():
    for slug, guide, points, maxw, maxh in SPECS:
        # Artwork source files live under assets/artworks/provided/
        artwork_dir = ROOT / 'assets/artworks/provided'
        element_work = OUT / 'element-work'
        element_work.mkdir(exist_ok=True)

        if guide == 'ni-zan':
            source = artwork_dir / '元_倪瓒_容膝斋图_1.jpg'
        else:
            source = element_work / f'{guide}-selection-guide.png'

        im = Image.open(source)
        if guide == 'ni-zan':
            points = [(x * im.width / 987, y * im.height / 2048) for x, y in points]
        x0 = min(x for x, y in points); y0 = min(y for x, y in points)
        x1 = max(x for x, y in points); y1 = max(y for x, y in points)
        scale = min(maxw / (x1 - x0), maxh / (y1 - y0))
        dx = 704 - (x1 + x0) * scale / 2; dy = 130 - (y1 + y0) * scale / 2
        pts = [(x * scale + dx, y * scale + dy) for x, y in points]
        path = 'M ' + ' L '.join(f'{x:.3f} {y:.3f}' for x, y in pts) + ' Z'
        shadow_svg = '<g transform="translate(2 3)">' + ''.join(
            f'<path d="{path}" fill="none" stroke="#304e46" stroke-opacity="{opacity}" '
            f'stroke-width="{width}" stroke-linejoin="round"/>'
            for width, opacity in [(12, .025), (8, .04), (4, .055)]
        ) + '</g>'
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="900" height="260" viewBox="0 0 900 260">\n'
            f'<defs><clipPath id="art"><path d="{path}"/></clipPath></defs>\n'
            f'{shadow_svg}\n'
            f'<path d="{path}" fill="none" stroke="#9b9e8c" stroke-width="7" stroke-linejoin="round"/>\n'
            f'<path d="{path}" fill="none" stroke="#faf6eb" stroke-width="5" stroke-linejoin="round"/>\n'
            f'<image x="{dx}" y="{dy}" width="{im.width * scale}" height="{im.height * scale}" '
            f'xlink:href="../element-work/{source.name}" clip-path="url(#art)"/>\n'
            f'</svg>'
        )
        import base64
        svg = svg.replace(
            '../element-work/' + source.name,
            ('data:image/jpeg;base64,' if source.suffix == '.jpg' else 'data:image/png;base64,')
            + base64.b64encode(source.read_bytes()).decode()
        )
        (ASSETS / f'{slug}-header.svg').write_text(svg, encoding='utf-8')

        pdf = element_work / f'{slug}-header.pdf'
        c = canvas.Canvas(str(pdf), pagesize=(900, 260))
        p = c.beginPath(); p.moveTo(pts[0][0], 260 - pts[0][1])
        for x, y in pts[1:]: p.lineTo(x, 260 - y)
        p.close(); c.setLineJoin(1)
        c.saveState(); c.translate(2, -3); c.setStrokeColor('#304e46')
        for width, opacity in [(12, .025), (8, .04), (4, .055)]:
            c.setStrokeAlpha(opacity); c.setLineWidth(width); c.drawPath(p, stroke=1, fill=0)
        c.restoreState()
        for color, width in [('#9b9e8c', 7), ('#faf6eb', 5)]:
            c.setStrokeColor(color); c.setLineWidth(width); c.drawPath(p, stroke=1, fill=0)
        c.saveState(); c.clipPath(p, stroke=0, fill=0)
        c.drawImage(ImageReader(im), dx, 260 - dy - im.height * scale,
                    width=im.width * scale, height=im.height * scale)
        c.restoreState(); c.showPage(); c.save()

        doc = fitz.open(pdf)
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2), alpha=True)
        preview = Image.frombytes('RGBA', (pix.width, pix.height), pix.samples)
        preview.resize((900, 260), Image.Resampling.LANCZOS).save(ASSETS / f'{slug}-header.png')

    (ASSETS / 'element-provenance.json').write_text(json.dumps({
        'method': ('Original source artwork in vector clipping paths; '
                   'no generative repainting or recoloring. PNGs render those vector compositions.'),
        'header_size': [900, 260],
        'shadow': {'offset': [2, 3], 'color': '#304e46', 'width_opacity': [[12, .025], [8, .04], [4, .055]]},
        'landscape_source': '北宋_范宽_溪山行旅图_1.jpg',
        'selections': [{'slug': s, 'guide': g, 'polygon': p} for s, g, p, _, _ in SPECS],
    }, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    build()
