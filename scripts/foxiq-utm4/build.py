import json,re,collections
from datetime import datetime,timedelta,timezone
def L(k):
    d=json.load(open(f"raw/{k}.json")); return [dict(zip(d['columns'],r)) for r in d['rows']]
def ts(s): return datetime.fromisoformat(s.replace('Z','+00:00')) if '+' in s or 'Z' in s else datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
TEST=re.compile(r'\+.*@|gox-media\.com|@yandex\.ru|test|@example\.com|mailinator|k\.k\.tarasova|nikitos\.gura|dariaivanova|eevakenn|nedvedyea|^kkk@gmail\.com$|^myskillhouse2020@gmail\.com$|^ekaasrirahmawati403@gmail\.com$|krippsi@yandex|themaximusversus')
MSK=timedelta(hours=3)
buy={}
for r in L('buyers'):
    e=r['email']; t=ts(r['timestamp'])
    if e not in buy or t<buy[e]['t']: buy[e]=dict(t=t,os=r['$os'],country=r['$geoip_country_code'],pid=r['person_id'])
fun=collections.defaultdict(list)
for r in L('funnel'): fun[r['email']].append((ts(r['timestamp']),r['utm_source'],r['utm_campaign']))
can=collections.defaultdict(list)
for r in L('cancels'): can[r['email']].append((ts(r['timestamp']),r['event'],r['reason']))
act=collections.defaultdict(list)
for r in L('activity'): act[r['email']].append((ts(r['timestamp']),r['event'],r['$pathname'] or ''))
rows=[];excl=collections.Counter()
for e,b in buy.items():
    if not e or TEST.search(e): excl['test']+=1; continue
    t=b['t']
    # funnel purchase closest before app purchase (within 48h), else closest overall
    f=[x for x in fun.get(e,[]) if x[0]<=t+timedelta(minutes=10)]
    f=max(f,key=lambda x:x[0]) if f else (min(fun[e],key=lambda x:abs((x[0]-t).total_seconds())) if fun.get(e) else None)
    if f and f[2] in ('88888888','{campaignid}'): excl['test_campaign']+=1; continue
    src=(f[1] if f else 'no_funnel') or 'none'
    ev=sorted(x for x in can.get(e,[]) if x[0]>=t-timedelta(minutes=1))
    exp=[x[0] for x in ev if x[1]=='subscription_expired']
    selfc=None;bank=None
    for x in ev:
        if x[1]=='subscription_cancelled':
            # bank failure: expired within 2 min
            if any(abs((y-x[0]).total_seconds())<=120 for y in exp): bank=bank or x[0]
            elif selfc is None: selfc=x[0]
    for y in exp:
        bank=bank or y if not selfc or y<selfc else bank
    renewed=any(x[1]=='subscription_renewed' for x in ev)
    a=[x for x in act.get(e,[]) if t-timedelta(minutes=5)<=x[0]<=t+timedelta(hours=1)]
    train=any(x[1] in('game_started','test_started','lesson_completed') for x in a)
    cert=any(x[1].startswith('certificate') or '/iq-certificate' in x[2] for x in a)
    entered=len(a)>0
    span=(max(x[0] for x in a)-min(x[0] for x in a)).total_seconds()/60 if a else 0
    a72=[x for x in act.get(e,[]) if t<=x[0]<=t+timedelta(hours=72)]
    days=len({(x[0]+MSK).date() for x in a72 if x[1] in('game_started','test_started','lesson_completed')})
    d=lambda c: (c-t).total_seconds()/3600 if c else None
    msk=(t+MSK)
    rows.append(dict(t=t.isoformat(),day=str(msk.date()),src=src,camp=(f[2] if f else None),os=b['os'],country=b['country'],
        c1h=bool(selfc and d(selfc)<1), c72=bool(selfc and d(selfc)<72), c_min=round((selfc-t).total_seconds()/60,1) if selfc else None,
        bank72=bool(bank and d(bank)<72), renewed=renewed, entered=entered, train=train, cert=cert, span=round(span,1), traindays72=days,
        full72=(t+timedelta(hours=72))<datetime(2026,11,24,8,0,tzinfo=timezone.utc)))
json.dump(rows,open('rows.json','w'),default=str)
print(len(rows),excl, collections.Counter(r['src'] for r in rows).most_common())
print(min(r['day'] for r in rows), max(r['day'] for r in rows))
