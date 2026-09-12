"""Generate the local search layout using the active skin's typography/assets."""
from pathlib import Path
import xml.etree.ElementTree as E
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
w = E.Element('window')
E.SubElement(w, 'defaultcontrol', always='true').text = '100'
cs = E.SubElement(w, 'controls')
WHITE = 'special://skin/extras/search-ui/white.png'
ROUND = 'special://skin/media/common/menu.png'
KEY = 'special://skin/extras/search-ui/key.png'
# A small primitive keeps the skin's soft corners within the actual key bounds.
# The original menu texture has 40px borders and expands a 60px-high control.
tile = Image.new('RGBA', (128, 128))
ImageDraw.Draw(tile).rounded_rectangle((0, 0, 127, 127), radius=48, fill='white')
tile.resize((32, 32), Image.Resampling.LANCZOS).save(ROOT/'extras/search-ui/key.png')

def control(parent, typ, id=None, **tags):
    c = E.SubElement(parent, 'control', {'type': typ, **({'id': str(id)} if id else {})})
    for key, value in tags.items():
        E.SubElement(c, key).text = str(value)
    return c

def image(parent, x, y, width, height, color, texture=WHITE, border=None):
    c = control(parent, 'image', left=x, top=y, width=width, height=height)
    E.SubElement(c, 'texture', colordiffuse=color, **({'border': str(border)} if border else {})).text = texture
    return c

def label(id, text, x, y, width, height, font='font_main', color='main_fg_100'):
    return control(cs, 'label', id, left=x, top=y, width=width, height=height,
                   font=font, textcolor=color, label=text)

image(cs, 0, 0, 1920, 1080, 'FF09090D')
label(None, '영화찾기', 80, 48, 440, 64, 'font_huge_bold')
label(None, '$INFO[System.Time]', 1650, 56, 190, 48, 'font_midi').append(E.Element('align'))
cs[-1].find('align').text = 'right'
image(cs, 80, 124, 1760, 1, 'main_fg_12')
label(None, '보유 영화와 시리즈', 80, 145, 480, 44, 'font_mini', 'main_fg_70')
image(cs, 640, 157, 1200, 84, 'main_fg_06', ROUND, 24)
label(10, '제목이나 초성으로 검색', 664, 172, 1152, 54, 'font_midi')
label(11, '최근 추가한 작품', 640, 259, 1160, 45, 'font_main_bold')
label(12, '오른쪽에서 작품을 선택하세요', 640, 1008, 1200, 42, 'font_tiny', 'main_fg_50')
label(None, '초성으로도 검색할 수 있어요', 80, 950, 480, 40, 'font_tiny', 'main_fg_50')
label(None, '예: ㅋㅋㄹㅂ → 콘클라베', 80, 987, 480, 40, 'font_tiny', 'main_fg_70')

def button(id, text, x, y, width, height, up, down, left, right):
    c = control(cs, 'button', id, label=text, left=x, top=y, width=width, height=height,
                font='font_main', textcolor='main_fg_90', focusedcolor='FF101014',
                textoffsetx=0, textoffsety=0, align='center', aligny='center',
                onup=up, ondown=down, onleft=left, onright=right)
    E.SubElement(c, 'texturefocus', colordiffuse='FFFFFFFF', border='12').text = KEY
    E.SubElement(c, 'texturenofocus', colordiffuse='main_fg_12', border='12').text = KEY
    return c

button(20, '영문/숫자', 80, 213, 228, 58, 24, 100, 24, 21)
button(21, '띄어쓰기', 320, 213, 228, 58, 24, 103, 20, 500)
for i in range(42):
    row, col = divmod(i, 6)
    cid = 100 + i
    c = button(cid, '', 80+col*80, 293+row*70, 68, 60,
               cid-6 if row else 20, cid+6 if row < 6 else 22,
               cid-1 if col else cid, cid+1 if col < 5 else 500)
    E.SubElement(c, 'visible').text = 'Control.IsEnabled(%s)' % cid
button(22, '지우기', 80, 803, 228, 58, 136, 24, 22, 23)
button(23, '모두 지우기', 320, 803, 228, 58, 139, 25, 22, 500)
button(24, '뒤로', 80, 879, 228, 58, 22, 24, 24, 25)
button(25, '결과 보기', 320, 879, 228, 58, 23, 25, 24, 500)
p = control(cs, 'panel', 500, left=640, top=322, width=1200, height=674,
            onleft=25, onup=500, ondown=500, onright=500,
            orientation='vertical', scrolltime=150, preloaditems=2)
for layout in ('itemlayout', 'focusedlayout'):
    l = E.SubElement(p, layout, width='240', height='337')
    if layout == 'focusedlayout':
        image(l, 0, 0, 208, 337, 'main_fg_100', KEY, 12)
    art = control(l, 'image', left=4, top=4, width=200, height=278, aspectratio='keep')
    E.SubElement(art, 'texture', background='true').text = '$INFO[ListItem.Art(poster)]'
    for y, font, text in ((284, 'font_tiny_bold', '$INFO[ListItem.Label]'), (311, 'font_hint', '$INFO[ListItem.Label2]')):
        control(l, 'label', left=8, top=y, width=192, height=26, font=font,
                textcolor='FF101014' if layout == 'focusedlayout' else 'main_fg_90',
                label=text, scroll='false')
E.indent(w)
E.ElementTree(w).write(ROOT/'extras/search-ui/resources/skins/Default/1080i/HomeKoSearch.xml', encoding='UTF-8', xml_declaration=True)
