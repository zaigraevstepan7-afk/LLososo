#!/usr/bin/env python3
"""Premium = 20 US + 20 CA reality servers, each VERIFIED by a real TLS handshake (with its SNI)."""
import re, base64, glob, json, ssl, socket, urllib.request, time, urllib.parse as up
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

def norm(t):
    if "://" in t: return t
    c = re.sub(r"\s+", "", t)
    try:
        d = base64.b64decode(c + "=" * (-len(c) % 4)).decode("utf-8", "ignore")
        return d if "://" in d else t
    except Exception: return t

URI = re.compile(r"vless://[^\s'\"<>]+")
RE_UUID = re.compile(r"^[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}$")
RE_PBK  = re.compile(r"^[A-Za-z0-9_-]{43}$")
RE_DOM  = re.compile(r"^[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
RE_HEX  = re.compile(r"[0-9a-fA-F]+")
VALID_FP = {"chrome","firefox","safari","ios","android","edge","360","qq","random","randomized"}
def clean_sid(s):
    h = (RE_HEX.match(s or "") or [""])[0] if not RE_HEX.match(s or "") else RE_HEX.match(s or "").group(0)
    h = h[:16];  return h[:-1] if len(h)%2 else h
def clean_flow(fl):
    if fl=="xtls-rprx-vision" or not fl: return fl
    return "xtls-rprx-vision" if "vision" in fl else ""
def parse(u):
    rest=u.split("://",1)[1]; frag=""
    if "#" in rest: rest,frag=rest.split("#",1)
    uid,_,host=rest.split("?",1)[0].partition("@")
    q=rest.split("?",1)[1] if "?" in rest else ""
    return uid,host,dict(up.parse_qsl(q))

socket.setdefaulttimeout(3)
cfgs, seen = [], set()
for f in glob.glob("srcs/*.raw"):
    for m in URI.findall(norm(open(f, encoding="utf-8", errors="ignore").read())):
        u=m.strip().rstrip(",").replace("&amp;","&")
        try: uid,host,par=parse(u)
        except Exception: continue
        if ":" not in host: continue
        if par.get("security")!="reality": continue
        if (par.get("type") or "tcp") not in ("tcp","grpc"): continue
        sni=par.get("sni") or par.get("serverName",""); pbk=par.get("pbk","")
        if not (RE_UUID.match(uid) and RE_PBK.match(pbk) and RE_DOM.match(sni)): continue
        addr,_,port=host.rpartition(":")
        if not port.isdigit() or not(0<int(port)<65536): continue
        if not RE_DOM.match(addr) and not re.match(r"^[0-9.]+$",addr): continue
        key=(addr,port,pbk)
        if key in seen: continue
        seen.add(key)
        fp=par.get("fp","chrome"); fp=fp if fp in VALID_FP else "chrome"
        cfgs.append({"uri":u,"uid":uid,"addr":addr,"port":int(port),"net":par.get("type") or "tcp",
                     "sni":sni,"flow":clean_flow(par.get("flow","")),"pbk":pbk,"sid":clean_sid(par.get("sid","")),
                     "fp":fp,"sname":par.get("serviceName","")})
print("reality candidates:", len(cfgs))

# resolve + geoip
addrs={c["addr"] for c in cfgs}; ip_of={}
def is_ip(a): return re.match(r'^[0-9.]+$',a)
for a in addrs:
    if is_ip(a): ip_of[a]=a
    else:
        try: ip_of[a]=socket.gethostbyname(a)
        except Exception: ip_of[a]=None
ips=sorted({v for v in ip_of.values() if v}); geo={}
for i in range(0,len(ips),100):
    body=json.dumps([{"query":ip,"fields":"query,countryCode"} for ip in ips[i:i+100]]).encode()
    req=urllib.request.Request("http://ip-api.com/batch",data=body,headers={"Content-Type":"application/json"})
    try:
        for r in json.load(urllib.request.urlopen(req,timeout=30)): geo[r.get("query")]=r.get("countryCode")
    except Exception as e: print("geoip err",e)
    time.sleep(1.5)
for c in cfgs: c["cc"]=geo.get(ip_of.get(c["addr"]))
usca=[c for c in cfgs if c["cc"] in ("US","CA")]
print("US/CA candidates:", Counter(c["cc"] for c in usca))

# real TLS handshake test with the server's SNI
def tls_ok(c):
    ip=ip_of.get(c["addr"])
    if not ip: return None
    ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    try:
        t0=time.monotonic()
        with socket.create_connection((ip,c["port"]),timeout=6) as s:
            with ctx.wrap_socket(s,server_hostname=c["sni"]) as ss:
                ss.do_handshake()
                return (time.monotonic()-t0)*1000
    except Exception:
        return None
with ThreadPoolExecutor(max_workers=100) as ex:
    res=list(ex.map(tls_ok, usca))
ok=[]
for c,r in zip(usca,res):
    if r is not None: c["rtt"]=r; ok.append(c)
print(f"TLS-handshake PASSED: {len(ok)}/{len(usca)} ", dict(Counter(c['cc'] for c in ok)))

def take(cc,n):
    return sorted([c for c in ok if c["cc"]==cc], key=lambda e:e["rtt"])[:n]
PREM = take("US",20) + take("CA",20)
print("PREMIUM verified:", dict(Counter(c['cc'] for c in PREM)), "| total", len(PREM))
json.dump({"prem":PREM},open("/tmp/prem.json","w"))
