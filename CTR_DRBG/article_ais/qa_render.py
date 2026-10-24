"""Local PDF QA helper. Requires PyMuPDF and Pillow; not a mathematical check."""
from pathlib import Path
import json
import fitz
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parent
qa = root/'qa'
qa.mkdir(exist_ok=True)
doc = fitz.open(root/'main.pdf')
text = '\n'.join(page.get_text() for page in doc)
assert '??' not in text, 'unresolved reference in PDF'
outside = []
thumbs = []
for index, page in enumerate(doc):
    pix = page.get_pixmap(matrix=fitz.Matrix(1.4, 1.4), alpha=False)
    path = qa/f'page-{index+1:02d}.png'
    pix.save(path)
    for word in page.get_text('words'):
        x0,y0,x1,y1,*_ = word
        if x0 < 28 or x1 > page.rect.width-28 or y0 < 20 or y1 > page.rect.height-18:
            outside.append({'page': index+1, 'word': word[4], 'rect': list(word[:4])})
    thumb = Image.open(path).convert('RGB')
    thumb.thumbnail((298, 422))
    panel = Image.new('RGB', (322,454), 'white')
    panel.paste(thumb, ((322-thumb.width)//2, 22))
    ImageDraw.Draw(panel).text((10,5), f'Page {index+1}', fill='black')
    thumbs.append(panel)
for start in range(0, len(thumbs), 9):
    group = thumbs[start:start+9]
    sheet = Image.new('RGB', (322*3,454*((len(group)+2)//3)), '#d4d4d4')
    for index, panel in enumerate(group):
        sheet.paste(panel, ((index%3)*322, (index//3)*454))
    sheet.save(qa/f'contact-{start//9+1}.png')
assert not outside, outside
log = (root/'main.log').read_text(encoding='utf-8', errors='replace')
assert 'Overfull' not in log
assert 'undefined' not in log.lower()
report = {'pages': len(doc), 'unresolved_references': 0, 'words_outside_safety_margin': 0,
          'overfull_boxes': 0, 'visual_inspection': 'pending',
          'text_characters': len(text)}
(qa/'extracted.txt').write_text(text, encoding='utf-8')
(qa/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
