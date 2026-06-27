#!/usr/bin/env python3
"""Gaming config for users in Russia behind DPI: NEARBY servers + whitelist/Yandex SNI (low ping + bypass)."""
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
    m = RE_HEX.match(s or ""); h = m.group(0) if m else ""
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

WL_HINTS = ("yandex","ozon","vk.com","vk.ru","id.vk","mail.ru","kinopoisk","avito","pervye.ru",
 "genproc.gov.ru","gosuslugi","sberbank","sber.ru","x5.ru","rbc.ru","gismeteo","2gis","rutube",
 "tinkoff","tbank","wildberries","mos.ru","max.ru","kontur","ngenix.net")
def wl_score(sni):
    s=sni.lower()
    if "yandex" in s: return 100
    if s.endswith(".ru") or any(h in s for h in WL_HINTS): return 60
    return 0
# proximity to Moscow (lower ping). tiers -> bonus
PROX = {**{c:30 for c in ("FI","EE","LV","LT","BY","UA","KZ","GE","AM","AZ")},
        **{c:22 for c in ("SE","NO","PL","DE","CZ","AT","HU","SK","MD","TR","RO")},
        **{c:12 for c in ("NL","CH","FR","BE","DK","BG","RS","HR","SI","IT","GB","GR","ES")}}
NEAR = set(PROX)  # only nearby countries
CCN = {"FI":"Finland","EE":"Estonia","LV":"Latvia","LT":"Lithuania","BY":"Belarus","UA":"Ukraine",
 "KZ":"Kazakhstan","GE":"Georgia","AM":"Armenia","AZ":"Azerbaijan","SE":"Sweden","NO":"Norway",
 "PL":"Poland","DE":"Germany","CZ":"Czechia","AT":"Austria","HU":"Hungary","SK":"Slovakia","MD":"Moldova",
 "TR":"Turkey","RO":"Romania","NL":"Netherlands","CH":"Switzerland","FR":"France","BE":"Belgium",
 "DK":"Denmark","BG":"Bulgaria","RS":"Serbia","HR":"Croatia","SI":"Slovenia","IT":"Italy",
 "GB":"United Kingdom","GR":"Greece","ES":"Spain"}

socket.setdefaulttimeout(3)
cfgs, seen = [], set()
for f in glob.glob("srcs/*.raw"):
    for m in URI.findall(norm(open(f, encoding="utf-8", errors="ignore").read())):
        u=m.strip().rstrip(",").replace("&amp;","&")
        try: uid,host,par=parse(u)
        except Exception: continue
        if ":" not in host or par.get("security")!="reality": continue
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
                     "fp":fp,"sname":par.get("serviceName",""),"wl":wl_score(sni)})
print("reality candidates:", len(cfgs))

addrs={c["addr"] for c in cfgs}; ip_of={}
for a in addrs:
    if re.match(r'^[0-9.]+$',a): ip_of[a]=a
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
near=[c for c in cfgs if c["cc"] in NEAR]
print("nearby candidates:", len(near), "| with whitelist SNI:", sum(1 for c in near if c["wl"]))

def tls_ok(c):
    ip=ip_of.get(c["addr"])
    if not ip: return None
    ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    try:
        with socket.create_connection((ip,c["port"]),timeout=6) as s:
            with ctx.wrap_socket(s,server_hostname=c["sni"]) as ss:
                ss.do_handshake(); return True
    except Exception:
        return False
with ThreadPoolExecutor(max_workers=120) as ex:
    res=list(ex.map(tls_ok, near))
alive=[c for c,ok in zip(near,res) if ok]
print("alive (TLS ok):", len(alive), "| whitelist-SNI alive:", sum(1 for c in alive if c["wl"]))

# rank: whitelist SNI first (DPI bypass), then proximity (low ping). app measures real ping on device.
def score(e): return e["wl"] + PROX.get(e["cc"],0)
alive.sort(key=lambda e: -score(e))
GAME = alive[:80]
print("GAME servers:", len(GAME), "| countries:", dict(Counter(c['cc'] for c in GAME)),
      "| whitelist:", sum(1 for c in GAME if c["wl"]))
json.dump({"game":GAME,"CCN":CCN},open("/tmp/game.json","w"))
