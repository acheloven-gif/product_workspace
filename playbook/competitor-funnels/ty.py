import json,subprocess,sys,time
def get(params):
    args=["curl","-s","-m","120","-G","https://api.tyver.io/creatives/"]
    for k,v in params.items(): args+=["--data-urlencode",f"{k}={v}"]
    for a in range(3):
        r=subprocess.run(args,capture_output=True,text=True)
        try:
            d=json.loads(r.stdout)
            if "items" in d: return d
        except Exception: pass
        time.sleep(3)
    return {"items":[],"error":r.stdout[:300]}
out={}
for dom in sys.argv[1:]:
    items=[];tot=None
    for page in (1,2,3,4,5):
        d=get({"domain":dom,"sort_by":"impressions_from","first_appearance":"2026-10-28","last_appearance":"2026-11-27","size":100,"page":page})
        if "error" in d: print(dom,"ERR",d["error"][:150]);break
        tot=d.get("total",tot); items+=d["items"]
        if len(d["items"])<100: break
    out[dom]={"total":tot,"items":items,"left":d.get("remainder_views")}
    print(dom,tot,len(items),d.get("remainder_views"),flush=True)
json.dump(out,open("ty_raw.json","w"))
