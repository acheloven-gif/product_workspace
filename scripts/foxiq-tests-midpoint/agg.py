import json,re,collections
from datetime import datetime,timedelta
L=lambda k: json.load(open(f"raw/{k}.json"))["rows"]
T=re.compile(r"\+.*@|gox-media\.com|@yandex\.ru|test|@example\.com|mailinator|k\.k\.tarasova|nikitos\.gura|dariaivanova|eevakenn|nedvedyea|^kkk@gmail\.com$|^myskillhouse2020@gmail\.com$|^ekaasrirahmawati403@gmail\.com$")
ts=lambda s: datetime.fromisoformat(s.replace("Z","+00:00")[:26].rstrip('+') if False else s.replace("Z","+00:00"))
START=ts("2026-11-18T09:30:00Z")
buy={}
for pid,em,t,it,env,trial,price in L("buyers"):
    if not em or T.search(em) or it is True or env=='dev': continue
    t=ts(t)
    if t<START: continue
    buy.setdefault(em,{"t":t,"pid":pid,"price":price,"trial":trial})
act=collections.defaultdict(list)
for em,pid,ev,t,v1,v3,sc,it,env in L("activity"):
    if em in buy: act[em].append((ts(t),ev,v1 if v1 not in ('None','') else None,v3 if v3 not in ('None','') else None,sc))
subs=collections.defaultdict(list)
for pid,em,ev,t,reason in L("subs"):
    if em in buy: subs[em].append((ts(t),ev,reason))
rows=[]
for em,b in sorted(buy.items(),key=lambda x:x[1]["t"]):
    a=sorted(act[em]); t0=b["t"]
    after=[x for x in a if x[0]>=t0-timedelta(minutes=30)]
    v1=next((x[2] for x in after if x[2]),None); v3=next((x[3] for x in after if x[3]),None)
    score=next((x[4] for x in after if x[1]=='iq_result_shown' and x[4] not in ('None','')),None)
    h=[x for x in a if t0<=x[0]<t0+timedelta(hours=1)]
    h2=[x for x in a if t0-timedelta(minutes=30)<=x[0]<t0+timedelta(hours=1)]
    train=any(x[1] in('game_started','test_started','lesson_started','lesson_completed') for x in h2)
    name=any(x[1]=='certificate_name_submitted' for x in h2)
    entered=len(after)>0
    s=sorted(subs[em]); 
    canc=next((x[0] for x in s if x[1] in('subscription_cancel_confirm','subscription_cancelled') and x[0]>=t0),None)
    c1h= canc is not None and (canc-t0)<timedelta(hours=1)
    refund=any(x[1] in('purchase_refunded','primer_refund') for x in s)
    renewed=any(x[1]=='subscription_renewed' for x in s)
    rows.append(dict(email=em,t=t0.isoformat(),v1=v1,v3=v3,score=score,entered=entered,train1h=train,name1h=name,cancel1h=c1h,cancelled=canc is not None,refund=refund,renewed=renewed,age_h=None))
json.dump(rows,open("raw/rows.json","w"),default=str,indent=0)
print(len(rows))
for r in rows: print(r["t"][:16],r["v1"],r["v3"],r["score"],"in" if r["entered"] else "--","T" if r["train1h"] else ".","N" if r["name1h"] else ".","C1h" if r["cancel1h"] else ("C" if r["cancelled"] else "."),"R" if r["refund"] else "", "ren" if r["renewed"] else "")
