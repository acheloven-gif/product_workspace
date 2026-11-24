import json,collections,datetime as D
rows=json.load(open('rows.json'))
rows=[r for r in rows if not (r['country']=='AM' and r['day']=='2026-10-28')]
rows=[r for r in rows if '2026-10-16'<=r['day']<='2026-11-18']
def wk(d):
    d=D.date.fromisoformat(d); m=d-D.timedelta(days=d.weekday()); return f"{m:%d.%m}–{m+D.timedelta(days=6):%d.%m}"
def g(r): return '4' if r['src']=='4' else ('нет воронки' if r['src']=='no_funnel' else 'другие')
def pc(a,b): return f"{a}/{b} ({a/b*100:.0f}%)" if b else "—"
tab=collections.defaultdict(list)
for r in rows: tab[(wk(r['day']),g(r))].append(r)
print("неделя | группа | n | отмена<1ч | отмена<72ч* | банк<72ч | зашли 1ч | трен 1ч | серт 1ч | медиана мин активн 1ч(зашедшие)")
import statistics as S
for k in sorted(tab,key=lambda k:(D.datetime.strptime(k[0][:5]+'.2026','%d.%m.%Y'),k[1])):
    v=tab[k]; f=[r for r in v if r['full72']]
    sp=[r['span'] for r in v if r['entered']]
    print(k[0],'|',k[1],'|',len(v),'|',pc(sum(r['c1h'] for r in v),len(v)),'|',pc(sum(r['c72'] for r in f),len(f)),'|',pc(sum(r['bank72'] for r in f),len(f)),'|',pc(sum(r['entered'] for r in v),len(v)),'|',pc(sum(r['train'] for r in v),len(v)),'|',pc(sum(r['cert'] for r in v),len(v)),'|',round(S.median(sp),1) if sp else '—')
print(collections.Counter(r['day'] for r in rows if r['src']=='no_funnel'))
