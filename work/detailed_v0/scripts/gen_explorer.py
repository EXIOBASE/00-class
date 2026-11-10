"""Build the interactive explorer page from industries_v0.csv / products_v0.csv.

Run after build.py and options.py: python -I scripts/gen_explorer.py
Writes explorer/exiobase_detailed_classification.html, which is published at
https://claude.ai/artifact/SJCDVSHpovi1yQxR3E52UF
"""
import json, html, re, datetime, os, pandas as pd
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ind=pd.read_csv(W+r'\industries_v0.csv',dtype=str).fillna('')
pro=pd.read_csv(W+r'\products_v0.csv',dtype=str).fillna('')
h=pd.read_csv(W+r'\refs\nace21_headings.tsv',sep='\t',dtype=str,usecols=['NACE_CODE','EN_DESC']).fillna('')
names={}; div_section={}; sec=None
for c,n in zip(h.NACE_CODE.str.strip('"'),h.EN_DESC.str.strip('"')):
    n=n[:1]+n[1:].lower() if n.isupper() else n
    names[c]=n
    if re.fullmatch(r'[A-Z]',c): sec=c
    elif re.fullmatch(r'\d\d',c): div_section[c]=sec
ex=pd.read_excel(r'D:\GitHub\EXIOBASE\00-class\class\exio3class.xlsx',sheet_name='industries',dtype=str)
exn=dict(zip(ex.CodeNr,ex.Name)); exo={c:i for i,c in enumerate(ex.CodeNr)}
icols=['code','name','section','nace21_class','nace21_name','isic5_class','isic4_classes','exio3_industry_code','exio3_industry_name','exio3_map_basis','split_reason','principal_products','data_anchors','tier','notes','option_b_code','option_b_name']
pcols=['code','name','cpc21','cpc30','cpa_code','hs_hint','exio3_product_code','exio3_product_name','producing_industries','source_detail','data_anchors','tier','notes','option_b_code','option_b_name']
for c in icols:
    if c not in ind: ind[c]=''
about=''
try:
    md=open(W+r'\summary.md',encoding='utf-8').read()
    out=[];inlist=False
    for line in md.splitlines():
        l=line.rstrip()
        if l.startswith('- ') or l.startswith('* ') or re.match(r'^\d+\. ',l):
            if not inlist: out.append('<ul>'); inlist=True
            out.append('<li>'+html.escape(re.sub(r'^(- |\* |\d+\. )','',l))+'</li>'); continue
        if inlist: out.append('</ul>'); inlist=False
        if l.startswith('#'): out.append('<h3>'+html.escape(l.lstrip('#').strip())+'</h3>')
        elif l.startswith('|'): out.append('<p class="mono">'+html.escape(l)+'</p>')
        elif l: out.append('<p>'+html.escape(l)+'</p>')
    if inlist: out.append('</ul>')
    about='\n'.join(out).replace('**','')
except FileNotFoundError:
    about='<p>Summary not yet written.</p>'
D={'industries':ind[icols].to_dict('records'),'products':pro[pcols].to_dict('records'),'names':names,'div_section':div_section,
   'exio3_ind_names':exn,'exio3_ind_order':exo,'exio3_ind_count':len(ex),'about_html':about}
js=json.dumps(D,ensure_ascii=False).replace('</','<\/')
t=open(W+r'\explorer\template.html',encoding='utf-8').read()
t=t.replace('__DATA__',js).replace('__DATE__',datetime.date.today().isoformat())
bad=[c for c in ('\u2014','\u2013') if c in t]
open(W+r'\explorer\exiobase_detailed_classification.html','w',encoding='utf-8').write(t)
print(len(t)//1024,'KB; dashes present:',bad, len(ind), len(pro))
