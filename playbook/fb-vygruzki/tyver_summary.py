"""Сводка tyver_raw.json → tyver_summary.json (ёмкость ниш и гео). Запуск: python3 -I tyver_summary.py <dir с tyver_raw.json>"""
import json, sys, collections
D = sys.argv[1]
raw = json.load(open(f"{D}/tyver_raw.json"))
STORES = ("play.google.com","apps.apple.com","itunes.apple.com","w2a.one","onelink.me","app.adjust.com","apps.microsoft.com")
SOCIAL = ("facebook.com","fb.me","instagram.com","m.me","wa.me","api.whatsapp.com","youtube.com","tiktok.com","l.facebook.com","")
THR = 600_000
def kind(h):
    if any(h==s or h.endswith("."+s) for s in STORES): return "store"
    if any(h==s or h.endswith("."+s) for s in SOCIAL if s): return "social"
    if not h: return "social"
    return "web"
out = {"window": raw["window"], "products": {}}
for prod, kws in raw["kw"].items():
    own = raw["dom"][prod]["domain"]
    pdom = collections.defaultdict(lambda: {"reach":0,"ads":0,"pages":collections.Counter(),"kws":set()})
    krows = []
    for kw, r in kws.items():
        dom = collections.defaultdict(lambda: {"reach":0,"ads":0,"pages":collections.Counter()})
        rs = collections.Counter()
        for i in r["items"]:
            h = i["host"]; k = kind(h); rs[k] += i["impressions_from"] or 0
            if k != "web": continue
            for x in (dom[h], pdom[h]):
                x["reach"] += i["impressions_from"] or 0; x["ads"] += 1; x["pages"][i["provider_page_name"] or ""] += 1
            pdom[h]["kws"].add(kw)
        top = sorted(dom.items(), key=lambda kv: -kv[1]["reach"])
        krows.append({"kw":kw, "total":r["total"], "sample":len(r["items"]), "web_domains":len(dom),
            "big_domains":sum(1 for _,v in top if v["reach"]>=THR), "reach_web":rs["web"], "reach_store":rs["store"],
            "own_in_sample": any(h==own or h.endswith("."+own) or own.endswith(h) and h.count(".")>=1 and h.split(".")[-2]==own.split(".")[-2] for h in dom),
            "top": [{"domain":h,"reach":v["reach"],"ads":v["ads"],"page":v["pages"].most_common(1)[0][0]} for h,v in top[:3]]})
    top = sorted(pdom.items(), key=lambda kv: -kv[1]["reach"])
    big = [h for h,v in top if v["reach"]>=THR]
    out["products"][prod] = {"own_domain": own, "kw": krows, "web_domains": len(pdom), "big_domains": len(big),
        "ads_30d_sum": sum(k["total"] or 0 for k in krows),
        "top": [{"domain":h,"reach":v["reach"],"ads":v["ads"],"page":v["pages"].most_common(1)[0][0],"kws":sorted(v["kws"])} for h,v in top[:6]]}
# гео по домену
for prod, r in raw["dom"].items():
    own = r["domain"]; base = own.split(".")[-2]
    items = [i for i in r["items"] if i["host"]==own or i["host"].endswith("."+own) or (base in i["host"])]
    single = collections.Counter(); single_reach = collections.Counter(); anyc = collections.Counter(); multi = 0
    for i in items:
        c = i["countries"] or []
        if len(c)==1: single[c[0]] += 1; single_reach[c[0]] += i["impressions_from"] or 0
        elif len(c)>1: multi += 1
        for x in c: anyc[x] += 1
    ns = sum(single.values()); n = len(items)
    out["products"][prod]["geo"] = {"total_api": r["total"], "sample": len(r["items"]), "matched": n,
        "active": sum(1 for i in items if i["is_active"]), "reach": sum(i["impressions_from"] or 0 for i in items),
        "single_n": ns, "multi_n": multi, "no_country": n-ns-multi,
        "single_share": [(c, round(100*v/ns)) for c,v in single.most_common(5)] if ns else [],
        "langs": collections.Counter(l for i in items for l in (i["languages"] or [])).most_common(4),
        "first": min((i["first_active_date"] for i in items if i["first_active_date"]), default=None),
        "hosts": collections.Counter(i["host"] for i in items).most_common(4)}
json.dump(out, open(f"{D}/tyver_summary.json","w"), ensure_ascii=False, indent=1)
for p,v in out["products"].items():
    g=v["geo"]; print(f"{p}: web domains {v['web_domains']}, ≥600k {v['big_domains']}; geo n={g['matched']}/{g['total_api']} active={g['active']} single={g['single_n']} {g['single_share']} langs={g['langs']} hosts={g['hosts']}")
