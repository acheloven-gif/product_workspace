import openpyxl,collections
SRC='/home/user/product-workspace/reports/fb-kandidaty-itog-10-10.xlsx'
wb=openpyxl.load_workbook(SRC,data_only=True)
rows=list(wb['Сводная (все строки)'].iter_rows(values_only=True))[1:]
MON={'18.05':'Май','29.06':'Июнь','28.07':'Июль','27.08':'Август','28.08':'Август','10.10':'Октябрь'}
def scheme(u):
    u=(u or '').lower()
    return 'стор' if any(k in u for k in ['apps.apple','itunes.apple','play.google']) else 'веб'
# per app, month, scheme: dedupe pixel within month (Aug has 2 exports): keep row with max spend per (pixel,landing scheme)
agg=collections.defaultdict(dict)
for r in rows:
    app,date,pix,sp,cpa,conv=r[0],r[3],r[5],r[11] or 0,r[16],r[21]
    m=MON[date]; s=scheme(r[47])
    key=(app,m,s,pix,r[47] if False else None)
    d=agg[(app,m,s)]
    k=(pix,r[2])
    d.setdefault('rows',[]).append((r[2],pix,sp,cpa,conv))
def summarize(app,m,s):
    d=agg.get((app,m,s))
    if not d: return None
    # dedupe pixel across exports in same month: per pixel keep export with max spend sum
    byexp=collections.defaultdict(lambda:collections.defaultdict(lambda:[0,0,0]))
    for exp,pix,sp,cpa,conv in d['rows']:
        t=byexp[pix][exp]; t[0]+=sp; t[1]+=(conv or 0); t[2]+= (0 if conv else 1)
    sp=cv=miss=0
    for pix,exps in byexp.items():
        e=max(exps.values(),key=lambda t:t[0]); sp+=e[0]; cv+=e[1]; miss+=e[2]
    return dict(spend=sp,conv=cv,cpa=(sp/cv if cv else None),miss=miss)
