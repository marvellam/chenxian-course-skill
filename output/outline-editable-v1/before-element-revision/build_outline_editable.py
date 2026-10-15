"""Build live-text HTML plus static proofs from the editable outline JSON.
Proofs are Pillow composition checks, not browser screenshots.
"""
from pathlib import Path
import json, re, html, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output/outline-editable-v1'
ASSETS=OUT/'assets'
DATA=json.loads((OUT/'content.json').read_text(encoding='utf-8'))
FONTS=Path.home()/'AppData/Local/Microsoft/Windows/Fonts'
PAPER='#f1ebdf'; INK='#304e46'; BODY='#46534d'; MUTED='#69766b'; LINE='#b6b9a9'
FACES={'sans':'SourceHanSans-Regular.ttc','medium':'SourceHanSans-Medium.ttc','serif':'SourceHanSerifCN-Heavy-4.otf'}
CSS_FACES={'sans':'"Source Han Sans CN","Source Han Sans SC",sans-serif','medium':'"Source Han Sans CN","Source Han Sans SC",sans-serif','serif':'"Source Han Serif CN",serif'}
def font(size,face='sans'): return ImageFont.truetype(str(FONTS/FACES[face]),size)
def esc(text): return html.escape(text,quote=True)

def wrap(text,size,width,face='sans'):
    f=font(size,face); lines=[]
    while text:
        n=1
        while n<len(text) and f.getlength(text[:n+1])<=width: n+=1
        while n>1 and ((n<len(text) and text[n] in '，。、；：！？）》”') or text[n-1] in '《（“'): n-=1
        if 0<len(text)-n<=2: n-=2
        lines.append(text[:n]); text=text[n:]
    assert all(f.getlength(s)<=width for s in lines)
    return lines

# Chapter decoration uses existing paintings with soft edge masks only.
specs=[
 ('landscape','北宋_范宽_溪山行旅图_1.jpg',(.16,.18,.88,.63),'cover'),
 ('flower','南宋_吴炳_出水芙蓉图_1.jpg',(.10,.10,.91,.95),'cover'),
 ('figure','南宋_梁楷_泼墨仙人图_1.jpg',(.533,.29,.819,.89),'contain'),
]
for slug,name,crop,mode in specs:
    src=Image.open(ROOT/'assets/reference-paintings'/name).convert('RGB')
    box=tuple(round(v*(src.width if i%2==0 else src.height)) for i,v in enumerate(crop))
    art=src.crop(box)
    if mode=='cover': art=ImageOps.fit(art,(500,260),method=Image.Resampling.LANCZOS)
    else:
        art.thumbnail((390,260),Image.Resampling.LANCZOS)
    w,h=art.size
    xx=np.arange(w)[None,:]; yy=np.arange(h)[:,None]
    mask=np.minimum(np.clip(xx/100,0,1),np.clip((w-1-xx)/28,0,1))
    mask=mask*np.minimum(np.clip(yy/24,0,1),np.clip((h-1-yy)/38,0,1))
    mask=(mask*.48*255).astype('uint8')
    bg=Image.new('RGB',(900,260),PAPER)
    bg.paste(art,(900-w,0),Image.fromarray(mask))
    bg.save(ASSETS/f'{slug}-header.png')

class Panel:
    def __init__(self):
        self.im=Image.new('RGB',(1080,7000),PAPER)
        self.d=ImageDraw.Draw(self.im); self.parts=[]; self.bottom=0; self.texts=[]
    def text(self,text,x,y,size=44,width=900,face='sans',color=BODY,leading=None,align='left',lines=None,tag='p',extra=''):
        lines=lines if lines is not None else wrap(text,size,width,face)
        assert ''.join(lines)==text
        leading=leading or round(size*1.45)
        f=font(size,face)
        for i,s in enumerate(lines):
            assert f.getlength(s)<=width,(s,width,size)
            xx=x+(width-f.getlength(s))/2 if align=='center' else x
            self.d.text((xx,y+i*leading),s,font=f,fill=color,anchor='lt')
        height=len(lines)*leading
        weight=900 if face=='serif' else 500 if face=='medium' else 400
        style=f'left:{x}px;top:{y}px;width:{width}px;font-family:{CSS_FACES[face]};font-size:{size}px;font-weight:{weight};line-height:{leading}px;color:{color};text-align:{align};'
        spans=''.join(f'<span style="display:block;white-space:pre;">{esc(s)}</span>' for s in lines)
        self.parts.append(f'<{tag} class="editable-copy" style="{esc(style)}" {extra}>{spans}</{tag}>')
        self.texts.append(text); self.bottom=max(self.bottom,y+height)
        return y+height
    def image(self,name,x,y,w,h):
        im=Image.open(ASSETS/name).convert('RGBA').resize((w,h),Image.Resampling.LANCZOS)
        self.im.paste(im,(x,y),im)
        self.parts.append(f'<img class="outline-decoration" src="assets/{name}" alt="" aria-hidden="true" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;">')
        self.bottom=max(self.bottom,y+h)
    def line(self,y,x=90,w=900):
        self.d.line((x,y,x+w,y),fill=LINE,width=1)
        self.parts.append(f'<div aria-hidden="true" style="position:absolute;left:{x}px;top:{y}px;width:{w}px;border-top:1px solid {LINE};"></div>')
    def label(self,text,x,y):
        self.d.rounded_rectangle((x,y,x+108,y+62),radius=7,fill=INK)
        self.parts.append(f'<div aria-hidden="true" style="position:absolute;left:{x}px;top:{y}px;width:108px;height:62px;background:{INK};border-radius:7px;"></div>')
        self.text(text,x,y+10,38,108,'medium',PAPER,50,'center')
    def heading(self,text,y):
        self.image('section-heading-frame@2x.png',312,y,456,80)
        self.text(text,312,y+7,52,456,'serif',INK,66,'center',tag='h2')
        return y+80
    def finish(self,name,tail=60):
        height=int(self.bottom+tail)
        self.im=self.im.crop((0,0,1080,height))
        self.im.save(OUT/f'{name}.png')
        self.im.resize((390,round(height*390/1080)),Image.Resampling.LANCZOS).save(OUT/f'{name}_390宽预览.png')
        return f'<section class="outline-panel" data-screen-label="{esc(name)}" style="height:{height}px;">'+''.join(self.parts)+'</section>',height

panels=[]; outlines=[]; metrics=[]
for idx,module in enumerate(DATA['modules']):
    p=Panel(); y=24
    if idx==0:
        y=p.heading('课程大纲',y)+42
        notice_lines=['课程更新中，大纲仅供参考，','以最终上线题目为准']
        y=p.text(DATA['notice'],90,y,40,900,'sans',MUTED,60,'center',lines=notice_lines)+54
    prefix,title=re.split(r'\s+',module['heading'],maxsplit=1)
    p.image(specs[idx][0]+'-header.png',90,y,900,260)
    p.text(prefix,115,y+43,36,350,'medium',MUTED,52)
    p.text(title,112,y+106,68,370,'serif',INK,88,tag='h3')
    y+=260; p.line(y)
    for lesson in module['lessons']:
        y+=24
        top=y
        p.text(f"第{lesson['number']}讲",90,y+2,40,136,'medium',INK,64)
        y=p.text(lesson['title'],242,y,44,748,'sans',BODY,64,extra=f'data-lesson="{idx+1}-{lesson["number"]}"')+24
        p.line(y)
        metrics.append({'module':idx+1,'number':lesson['number'],'title':lesson['title'],'top':top,'row_height':y-top,'font_size':44})
    name=f'课程大纲_{idx+1}_{title}'
    fragment,height=p.finish(name,70)
    outlines.append(fragment); panels.append((name,p.im));

def footer(platform):
    p=Panel(); y=p.heading('领取课程',28)+62
    for i,group in enumerate(DATA['claim'][platform]):
        if i:
            y=p.text('↓',90,y+4,38,900,'sans',MUTED,50,'center')+10
        for text in group:
            y=p.text(text,90,y,44,900,'medium',INK,64,'center')+6
    y+=30
    y=p.text(DATA['claim_tip'],100,y,38,880,'medium',INK,58,'center')+75
    y=p.heading('课程须知',y)+48
    for label,text in DATA['purchase_notes']:
        p.label(label,90,y+4)
        y=p.text(text,226,y,44,764,'sans',BODY,66)+34
    y+=20
    y=p.heading('常见问题',y)+48
    for question,answer in DATA['faq']:
        y=p.text(question,90,y,46,900,'medium',INK,68,tag='h3')+16
        y=p.text(answer,90,y,44,900,'sans',BODY,66)+40
        p.line(y); y+=36
    p.bottom=y
    name='课程须知与问题_'+('微信小店版' if platform=='wechat' else '小红书版')
    fragment,height=p.finish(name,40)
    return fragment,p.im,name

wechat,wechat_im,wechat_name=footer('wechat')
xhs,xhs_im,xhs_name=footer('xiaohongshu')
panels.append((wechat_name,wechat_im))

css='''
.outline-live { width:1080px; margin:0; background:#f1ebdf; }
.outline-panel { width:1080px; position:relative; overflow:hidden; background:#f1ebdf; }
.outline-live .editable-copy { position:absolute; margin:0; padding:0; border:0; letter-spacing:0; }
.outline-live .outline-decoration { position:absolute; display:block; }
'''
(OUT/'outline.css').write_text(css,encoding='utf-8')
def document(body,title):
    return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+'</title><link rel="stylesheet" href="outline.css"><style>html{background:#dedfda}body{margin:0}main{margin:0 auto!important}</style></head><body><main class="outline-live">'+body+'</main></body></html>'
for platform,tail in [('微信小店版',wechat),('小红书版',xhs)]:
    (OUT/f'课程大纲与须知_可编辑母版_{platform}.html').write_text(document(''.join(outlines)+tail,'中国美术史｜课程大纲与须知'),encoding='utf-8')

# The existing page gets real text nodes, not the PNG previews.
page=ROOT/'output/detail-entry-v1/课程入口_可编辑母版.html'
backup=OUT/'添加课程大纲前_详情页备份.html'
if not backup.exists(): shutil.copy2(page,backup)
source=page.read_text(encoding='utf-8')
if '.outline-live {' not in source: source=source.replace('  </style>',css+'  </style>',1)
body=(''.join(outlines)+wechat).replace('src="assets/','src="../outline-editable-v1/assets/')
section='<section class="outline-live" id="course-outline-live" aria-label="课程大纲与须知">'+body+'</section>'
if 'id="course-outline-live"' in source:
    start=source.index('<section class="outline-live" id="course-outline-live"')
    end=source.index('  </main>',start)
    source=source[:start]+section+'\n'+source[end:]
else: source=source.replace('  </main>',section+'\n  </main>',1)
page.write_text(source,encoding='utf-8')

# A compact inspection sheet and a contiguous reading proof.
thumbs=[]
for name,im in panels:
    thumbs.append(im.resize((390,round(im.height*390/1080)),Image.Resampling.LANCZOS))
sheet=Image.new('RGB',(390*4+24*3,max(t.height for t in thumbs)),PAPER)
for i,im in enumerate(thumbs): sheet.paste(im,(i*414,0))
sheet.save(OUT/'课程大纲与须知_并排检查.png')
full=Image.new('RGB',(1080,sum(im.height for _,im in panels)),PAPER)
y=0
for _,im in panels: full.paste(im,(0,y)); y+=im.height
full.save(OUT/'课程大纲与须知_整段预览.png')
manifest={'source_revision':DATA['source_revision'],'lecture_count':len(metrics),'counts':[len(m['lessons']) for m in DATA['modules']],
          'lesson_font':44,'faq_font':44,'notes':'Plain editable HTML text with independent image assets; PNG files are static composition proofs, not browser screenshots.',
          'main_page_platform':'wechat','metrics':metrics,'panels':[{'name':name,'size':list(im.size)} for name,im in panels]}
(OUT/'production.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'lectures':len(metrics),'panel_heights':[im.height for _,im in panels],'main_page_appended':True},ensure_ascii=False))
