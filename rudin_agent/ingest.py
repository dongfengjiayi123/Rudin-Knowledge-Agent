"""Deterministic PDF index. Numbered entries are indexed, not semantically verified."""
import hashlib
import re
import fitz
from .config import PDF_PATH

CHAPTERS = ['实数与复数系统','基本拓扑','数列与级数','连续性','微分','Riemann–Stieltjes 积分','函数序列与级数','一些特殊函数','多变量函数','微分形式的积分','Lebesgue 理论']
HEADING = re.compile(r'(?m)^(\d{1,2}\.\d+)\s+(Definition(?:s)?|Theorem|Proposition|Examples?|Remarks?|Notation|Corollary|Lemma)(?=[\s.(])')

def parse_pdf(path=PDF_PATH):
    doc = fitz.open(path)
    segments, pages, offset = [], [], 0
    for idx, page in enumerate(doc):
        txt = page.get_text(sort=False)
        # This uploaded edition has running headers followed by printed page numbers.
        match = re.search(r'^\s*\D[^\n]*\n(\d+)\s*\n', txt)
        printed = int(match.group(1)) if match else None
        pages.append({'pdf_page':idx+1,'printed_page':printed,'text':txt})
        segments.append((offset, offset+len(txt), idx+1))
        offset += len(txt)+1
    full = '\n'.join(p['text'] for p in pages)
    matches = list(HEADING.finditer(full))
    entries = []
    seen = set()
    for i,m in enumerate(matches):
        ref, label = m.group(1),m.group(2)
        chapter = int(ref.split('.')[0])
        if chapter < 1 or chapter > 11 or ref in seen:
            continue
        seen.add(ref)
        stop = matches[i+1].start() if i+1<len(matches) else len(full)
        body = full[m.start():stop]
        # Never attach exercises or the following chapter to the final entry.
        body = re.split(r'(?m)^EXERCISES\s*$|^Chapter\s+\d+',body)[0].strip()
        proof = re.split(r'(?m)^Proof[.\s]',body,maxsplit=1)[0].strip()
        start_page = next(pg for a,b,pg in segments if a<=m.start()<b)
        end_pos = m.start()+len(body)-1
        end_page = next((pg for a,b,pg in segments if a<=end_pos<=b),start_page)
        kind = 'definition' if label.startswith('Definition') else 'theorem' if label in ('Theorem','Proposition','Lemma','Corollary') else 'example' if label.startswith('Example') else 'remark'
        entries.append({'id':ref,'ref':ref,'kind':kind,'chapter':chapter,'title':f'{label} {ref}', 'aliases':[], 'statement':proof,'intuition':'自动索引的原文条目；数学公式可能存在 PDF 提取误差，请核对原书。','status':'indexed','source':{'pdf_page':start_page,'pdf_end':end_page,'printed_page':pages[start_page-1]['printed_page']},'raw':body})
    ids = {n['id'] for n in entries}
    edges = []
    for n in entries:
        for target in sorted(set(re.findall(r'(?:Theorems?|Definitions?|Propositions?|Lemma)\s+(\d{1,2}\.\d+)',n['raw']))):
            if target in ids and target!=n['id']:
                edges.append({'source':n['id'],'target':target,'relation':'references','status':'indexed','evidence':f'原文条目 {n["ref"]} 明确引用 {target}；尚未判断是否为证明依赖。'})
    return {'nodes':entries,'edges':edges,'pages':pages,'book':{'title':'Principles of Mathematical Analysis','author':'Walter Rudin','edition':'3','pdf_pages':len(doc),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}
