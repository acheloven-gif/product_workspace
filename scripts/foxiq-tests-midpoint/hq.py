import json,sys,urllib.request
def q(sql):
    req=urllib.request.Request("https://ph.app-inkfolio-reader.pro/api/projects/1/query/",data=json.dumps({"query":{"kind":"HogQLQuery","query":sql}}).encode(),headers={"Content-Type":"application/json","User-Agent":"curl/8.5.0"})
    d=json.load(urllib.request.urlopen(req,timeout=180))
    if 'results' not in d: raise SystemExit(d)
    return d['columns'],d['results']
if __name__=="__main__":
    c,r=q(sys.stdin.read()); print(c)
    for x in r[:int(sys.argv[1]) if len(sys.argv)>1 else 50]: print(x)
