"""Ёмкость ниши и гео через Tyver API (токен подставляет прокси среды; в коде токена нет).
Запуск: python3 -I tyver_capacity.py <out_dir>. Окно: объявления, показывавшиеся за 30 дней (first/last_appearance)."""
import json, sys, time, subprocess, collections
from urllib.parse import urlparse
OUT = sys.argv[1]
D_FROM, D_TO = "2026-10-21", "2026-11-20"
KW = {
 "Selfony": ["parenting quiz","parenting style","learn to be a parent","toddler tantrums","gentle parenting","mom guilt"],
 "AI Corso": ["ai course certificate","learn ai","ai journey","ai skills","chatgpt course","ai for beginners"],
 "AI Stats": ["ai sports predictions","ai betting picks","sports betting ai","betting tips app"],
 "Zeely": ["ai ads for business","ai marketing small business","ai ad creatives","ai video ads"],
 "Kodree": ["claude certificate","ai course certificate","data analytics course","learn ai skills"],
 "ProMuse": ["28-day ai program","ai challenge","personalized ai learning plan","ai certificate"],
 "Finestro": ["make money with ai","ai side hustle","ai freelance","earn with ai"],
 "TheRealIntro": ["what to say to her","flirting tips for men","texting girls","dating coach men"],
 "Muses Academy": ["get him back","make him want you","high value woman","attraction secrets"],
 "KitUp": ["book summaries 15 minutes","microlearning app","read more books"],
 "Educly": ["28-day ai challenge","15 minutes a day ai","learn ai from phone"],
 "BetterMe": ["attachment style quiz","anxious attachment","avoidant attachment","relationship quiz"],
 "Zenfy": ["escape 9 to 5","remote work ai","cansado de 9 a 5","trabajo remoto ia"],
 "MusesAcred": ["conviértete en la mujer","recuperar a tu ex","atraer a un hombre"],
 "Spilio": ["speak confidently","train of thought","public speaking practice","speech trainer","hablar con confianza"],
}
DOM = {"Selfony":"quiz.selfony.com","AI Corso":"quiz.ai-corso.com","AI Stats":"aistats.fnlfx.com","Zeely":"zeely.ai",
 "Kodree":"kodree.com","ProMuse":"promuse.ai","Finestro":"finestro.io","TheRealIntro":"therealintro.com",
 "Muses Academy":"quiz.musesacademy.io","KitUp":"quiz.kitup.net","Educly":"start.educly.app",
 "BetterMe":"betterme-relationshipplan.com","Zenfy":"zenfy.ac","MusesAcred":"quiz.musesacred.io","Spilio":"quiz.spilio.one"}
STORES = ("play.google.com","apps.apple.com","itunes.apple.com","w2a.one","onelink.me")
def get(params):
    args = ["curl","-s","-m","120","-G","https://api.tyver.io/creatives/"]
    for k,v in params.items(): args += ["--data-urlencode", f"{k}={v}"]
    for a in range(3):
        r = subprocess.run(args, capture_output=True, text=True)
        try:
            d = json.loads(r.stdout)
            if "items" in d: return d
        except Exception: pass
        time.sleep(3)
    return {"items":[], "total":None, "error": r.stdout[:300]}
def host(i):
    u = i.get("target_url") or ""
    h = urlparse(u).netloc.lower()
    return h[4:] if h.startswith("www.") else h
def slim(i):
    return {k:i.get(k) for k in ("provider_page_name","impressions_from","impressions_until","countries","first_active_date","last_active_date","is_active","target_url","languages","activity_days_amount")} | {"host":host(i)}
import os
RAW = f"{OUT}/tyver_raw.json"
res = json.load(open(RAW)) if os.path.exists(RAW) else {"window":[D_FROM,D_TO],"kw":{}, "dom":{}}
def done(r): return r.get("total") is not None and not r.get("partial")
def save(): json.dump(res, open(RAW,"w"), ensure_ascii=False)
base = {"sort_by":"impressions_from","first_appearance":D_FROM,"last_appearance":D_TO,"size":100}
for prod, kws in KW.items():
    for kw in kws:
        if done(res["kw"].get(prod,{}).get(kw,{})): continue
        items=[]; tot=None; bad=False
        for page in (1,2):
            d = get(base | {"search_query": f'"{kw}"', "page":page})
            if "error" in d: bad=True; break
            tot = d.get("total", tot); items += d["items"]
            if len(d["items"]) < 100: break
        if bad:
            print("STOP: API error", d["error"][:120], flush=True); save(); sys.exit(2)
        res["kw"].setdefault(prod,{})[kw] = {"total":tot,"items":[slim(i) for i in items], "views_left": d.get("remainder_views")}; save()
        print(prod, kw, tot, len(items), d.get("remainder_views"), flush=True)
for prod, dom in DOM.items():
    if done(res["dom"].get(prod,{})): continue
    items=[]; tot=None; bad=False
    for page in (1,2,3):
        d = get(base | {"domain": dom, "page":page})
        if "error" in d: bad=True; break
        tot = d.get("total", tot); items += d["items"]
        if len(d["items"]) < 100: break
    if bad:
        print("STOP: API error", d["error"][:120], flush=True); save(); sys.exit(2)
    res["dom"][prod] = {"domain":dom,"total":tot,"items":[slim(i) for i in items]}; save()
    print("DOM", prod, dom, tot, len(items), d.get("remainder_views"), flush=True)
save()
