#!/usr/bin/env python3
"""Build ROOT VPN configs: White-list (yandex), Normal (ordinary), Combined (both).
Each = stable auto-balancer Xray JSON (pick best on connect, freeze) + subscription txt."""
import re, base64, glob, json, urllib.parse as up
from collections import Counter, defaultdict

def norm(t):
    if "://" in t: return t
    c = re.sub(r"\s+", "", t)
    try:
        d = base64.b64decode(c + "=" * (-len(c) % 4)).decode("utf-8", "ignore")
        return d if "://" in d else t
    except Exception:
        return t

URI = re.compile(r"vless://[^\s'\"<>]+")
def f2cc(fr):
    r = [ord(c) - 0x1F1E6 for c in fr if 0x1F1E6 <= ord(c) <= 0x1F1FF]
    return (chr(65+r[0])+chr(65+r[1])) if len(r) >= 2 else None
CC = {"DE":"Germany","NL":"Netherlands","FR":"France","FI":"Finland","SE":"Sweden","US":"United States",
 "GB":"United Kingdom","CA":"Canada","CH":"Switzerland","LV":"Latvia","PL":"Poland","PH":"Philippines",
 "AT":"Austria","ES":"Spain","KZ":"Kazakhstan","RS":"Serbia","JP":"Japan","SG":"Singapore","KR":"South Korea",
 "IN":"India","TR":"Turkey","HK":"Hong Kong","RO":"Romania","IT":"Italy","CZ":"Czechia","HU":"Hungary",
 "EE":"Estonia","LT":"Lithuania","BG":"Bulgaria","AE":"UAE","IL":"Israel","NO":"Norway","DK":"Denmark",
 "IE":"Ireland","UA":"Ukraine","MD":"Moldova","SC":"Seychelles","AM":"Armenia","CY":"Cyprus","AU":"Australia"}
SKIP = {"RU","EU","AQ","UN"}
def flag(cc): return "".join(chr(0x1F1E6+ord(c)-65) for c in cc) if cc else "🌐"

WL_HINTS = ("yandex","ozon","vk.com","vk.ru","id.vk","mail.ru","kinopoisk","avito","pervye.ru",
 "genproc.gov.ru","gosuslugi","sberbank","sber.ru","x5.ru","rbc.ru","gismeteo","2gis","rutube",
 "tinkoff","tbank","wildberries","mos.ru","max.ru","kontur","ngenix.net")
def is_wl(sni):
    s = sni.lower()
    return "yandex" in s or s.endswith(".ru") or any(h in s for h in WL_HINTS)

def parse(u):
    rest = u.split("://",1)[1]; frag=""
    if "#" in rest: rest, frag = rest.split("#",1); frag = up.unquote(frag)
    uid, _, host = rest.split("?",1)[0].partition("@")
    q = rest.split("?",1)[1] if "?" in rest else ""
    return uid, host, dict(up.parse_qsl(q)), frag

# ---- field validators: drop/clean configs polluted by ad-text in sources ----
RE_UUID = re.compile(r"^[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}$")
RE_PBK  = re.compile(r"^[A-Za-z0-9_-]{43}$")           # x25519 public key, base64url, 43 chars
RE_DOM  = re.compile(r"^[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")  # plain domain SNI
RE_HEX  = re.compile(r"[0-9a-fA-F]+")
def clean_sid(sid):
    m = RE_HEX.match(sid or "")                       # keep only leading hex run
    h = m.group(0) if m else ""
    h = h[:16]                                         # reality shortId <= 16 hex chars
    if len(h) % 2: h = h[:-1]                          # must be even length
    return h
def valid(uid, pbk, sni):
    return RE_UUID.match(uid or "") and RE_PBK.match(pbk or "") and RE_DOM.match(sni or "")
def clean_flow(fl):
    if fl == "xtls-rprx-vision" or not fl: return fl   # only flow Xray accepts
    return "xtls-rprx-vision" if "vision" in fl else ""  # fix typos, clear unknown
VALID_FP = {"chrome","firefox","safari","ios","android","edge","360","qq","random","randomized"}

# ---- collect all reality servers (tcp/grpc), non-RU ----
all_cfgs, seen = [], set()
for f in glob.glob("srcs/*.raw"):
    for m in URI.findall(norm(open(f, encoding="utf-8", errors="ignore").read())):
        u = m.strip().rstrip(",").replace("&amp;", "&")
        try: uid, host, par, frag = parse(u)
        except Exception: continue
        if ":" not in host or len(uid) < 8: continue
        if par.get("security") != "reality": continue
        net = par.get("type") or "tcp"
        if net not in ("tcp","grpc"): continue
        sni = par.get("sni") or par.get("serverName","")
        pbk = par.get("pbk","")
        if not valid(uid, pbk, sni): continue          # skip configs with junk/ad-polluted fields
        cc = f2cc(frag)
        if cc in SKIP: continue
        addr, _, port = host.rpartition(":")
        if not port.isdigit() or not (0 < int(port) < 65536): continue
        if not RE_DOM.match(addr) and not re.match(r"^[0-9.]+$", addr): continue  # host must be domain or IP
        key = (addr, port, pbk)
        if key in seen: continue
        seen.add(key)
        fp = par.get("fp","chrome"); fp = fp if fp in VALID_FP else "chrome"
        all_cfgs.append({"uri":u,"uid":uid,"addr":addr,"port":int(port),"net":net,"sni":sni,"cc":cc,
                         "flow":clean_flow(par.get("flow","")),"pbk":pbk,"sid":clean_sid(par.get("sid","")),
                         "fp":fp,"sname":par.get("serviceName",""),"wl":is_wl(sni)})

print(f"Total reality servers (flag-filtered): {len(all_cfgs)}")

# ---- REAL geo-IP pass: resolve hosts, drop servers whose actual IP is in Russia ----
import socket, urllib.request, time
socket.setdefaulttimeout(3)
def is_ip(a): return re.match(r'^[0-9.]+$', a)
addrs = {c["addr"] for c in all_cfgs}
ip_of = {}
for a in addrs:
    if is_ip(a): ip_of[a] = a
    else:
        try: ip_of[a] = socket.gethostbyname(a)
        except Exception: ip_of[a] = None
ips = sorted({ip for ip in ip_of.values() if ip})
geo = {}
for i in range(0, len(ips), 100):
    chunk = ips[i:i+100]
    body = json.dumps([{"query": ip, "fields": "query,countryCode"} for ip in chunk]).encode()
    req = urllib.request.Request("http://ip-api.com/batch", data=body, headers={"Content-Type": "application/json"})
    try:
        for r in json.load(urllib.request.urlopen(req, timeout=30)):
            geo[r.get("query")] = r.get("countryCode")
    except Exception as e:
        print("geoip batch error:", e)
    time.sleep(1.5)

ISO2NAME = dict(CC)
kept = []
dropped_ru = 0
for c in all_cfgs:
    real = geo.get(ip_of.get(c["addr"]))
    if real == "RU":                       # actual server is in Russia -> exclude
        dropped_ru += 1; continue
    if real and real not in SKIP:          # trust real geo for label when known
        c["cc"] = real
    kept.append(c)
all_cfgs = kept
print(f"GeoIP: dropped {dropped_ru} RU-located servers | remaining: {len(all_cfgs)}")

# ---- LIVENESS: TCP-connect test every server, keep only reachable, record latency ----
from concurrent.futures import ThreadPoolExecutor
def probe(c):
    ip = ip_of.get(c["addr"])
    if not ip: return None
    s = socket.socket(); s.settimeout(2.5)
    t0 = time.monotonic()
    try:
        s.connect((ip, c["port"])); return (time.monotonic() - t0) * 1000
    except Exception:
        return None
    finally:
        s.close()
with ThreadPoolExecutor(max_workers=200) as ex:
    rtts = list(ex.map(probe, all_cfgs))
for c, rtt in zip(all_cfgs, rtts):
    c["rtt"] = rtt                         # ms if reachable, None if not (kept either way)
alive = sum(1 for c in all_cfgs if c["rtt"] is not None)
# liveness is a RANKING signal, not a hard filter: some servers block datacenter probes
# yet work fine on mobile, so we keep all but float reachable+fast ones to the top (proxy-1).
print(f"Liveness: {alive}/{len(all_cfgs)} reachable from here (used for ranking, not dropping)")
print(f"  white-list SNI: {sum(c['wl'] for c in all_cfgs)} | ordinary SNI: {sum(not c['wl'] for c in all_cfgs)}")

def pick(cands, n, prefer_yandex=False):
    """Country-diverse selection up to n, best first."""
    def sc(e):
        s = 0
        if prefer_yandex and "yandex" in e["sni"].lower(): s += 10
        if e["flow"].startswith("xtls-rprx-vision"): s += 3
        if e["cc"]: s += 2
        if e["net"] == "tcp": s += 1
        s += max(0, (500 - min(e.get("rtt") or 500, 500)) / 100)   # faster server = higher score (up to +5)
        return s
    cands = sorted(cands, key=lambda e: -sc(e))
    by = defaultdict(list)
    for e in cands: by[e["cc"] or "??"].append(e)
    order = sorted(by, key=lambda c: -sc(by[c][0]))
    out = []
    # round-robin across countries for spread
    while len(out) < n and any(by.values()):
        moved = False
        for c in order:
            if by[c]:
                out.append(by[c].pop(0)); moved = True
                if len(out) >= n: break
        if not moved: break
    return out[:n]

wl_pool   = [c for c in all_cfgs if "yandex" in c["sni"].lower()]            # white-list = yandex (proven)
norm_pool = [c for c in all_cfgs if not c["wl"]]                             # ordinary, non-whitelist SNI

WL   = pick(wl_pool, 100, prefer_yandex=True)
NORM = pick(norm_pool, 100)                                                  # 100 ordinary servers
ALL  = WL + NORM                                                             # all-in-one: white + normal (200)
# PREMIUM: 20 fastest live US + 20 fastest live Canada
def fastest(cc, n):
    c = sorted((e for e in all_cfgs if e["cc"] == cc), key=lambda e: (e.get("rtt") is None, e.get("rtt") or 9999))
    return c[:n]
PREM = fastest("US", 20) + fastest("CA", 20)
print(f"Premium: US={sum(1 for e in PREM if e['cc']=='US')} CA={sum(1 for e in PREM if e['cc']=='CA')}")

# ---- builders ----
RU_DIRECT = ["domain:ru","domain:xn--p1ai","geosite:category-ru","domain:yandex","domain:vk.com",
 "domain:userapi.com","domain:mail.ru","domain:ozon.ru","domain:wildberries.ru","domain:avito.ru",
 "domain:kinopoisk.ru","domain:gosuslugi.ru","domain:sberbank.ru","domain:tinkoff.ru","domain:2gis.com",
 "domain:rutube.ru","domain:max.ru","domain:yastatic.net","domain:yandexcloud.net","domain:mos.ru"]

def outbound(e, i):
    ss = {"network": e["net"], "security": "reality",
          "realitySettings": {"allowInsecure": False, "fingerprint": e["fp"] or "chrome",
              "publicKey": e["pbk"], "serverName": e["sni"], "shortId": e["sid"], "show": False},
          "sockopt": {"tcpKeepAliveInterval":15,"tcpKeepAliveIdle":30,"tcpMptcp":False}}
    if e["net"] == "grpc":
        ss["grpcSettings"] = {"serviceName": e["sname"], "multiMode": False}
    else:
        ss["tcpSettings"] = {"header": {"type": "none"}}
    return {"mux": {"enabled": False, "concurrency": -1}, "protocol": "vless",
        "settings": {"vnext": [{"address": e["addr"], "port": e["port"],
            "users": [{"encryption":"none","flow":e["flow"],"id":e["uid"],"level":8}]}]},
        "streamSettings": ss, "tag": f"proxy-{i+1}"}

def build_json(cfgs, remarks, path):
    cfgs = sorted(cfgs, key=lambda e: (e.get("rtt") is None, e.get("rtt") or 9999))   # fastest first => proxy-1 is best fallback
    proxies = [outbound(e,i) for i,e in enumerate(cfgs)]
    cfg = {
        "dns": {"servers": ["https://8.8.8.8/dns-query","https://8.8.4.4/dns-query"], "queryStrategy":"UseIP"},
        "inbounds": [
            {"listen":"127.0.0.1","port":10808,"protocol":"socks",
             "settings":{"auth":"noauth","udp":True,"userLevel":8},
             "sniffing":{"destOverride":["http","tls"],"enabled":True,"routeOnly":False},"tag":"socks"},
            {"listen":"127.0.0.1","port":10809,"protocol":"http","settings":{"userLevel":8},"tag":"http"}],
        "log": {"loglevel":"warning"},
        "outbounds": proxies + [
            {"protocol":"freedom","settings":{"domainStrategy":"UseIP"},"tag":"direct"},
            {"protocol":"blackhole","settings":{"response":{"type":"http"}},"tag":"block"}],
        "remarks": remarks,
        "routing": {"domainStrategy":"IPIfNonMatch","domainMatcher":"hybrid",
            "rules":[{"type":"field","protocol":["bittorrent"],"outboundTag":"direct"},
                {"type":"field","outboundTag":"direct","domain":RU_DIRECT},
                {"type":"field","network":"tcp,udp","balancerTag":"auto"}],
            "balancers":[{"tag":"auto","selector":["proxy-"],"strategy":{"type":"leastPing"},"fallbackTag":"proxy-1"}]},
        # stable: probe once on connect, freeze; re-pick only on reconnect
        "observatory": {"subjectSelector":["proxy-"],"probeURL":"https://www.gstatic.com/generate_204",
            "probeInterval":"9000h","enableConcurrency":True},
    }
    json.dump(cfg, open(path,"w"), ensure_ascii=False, indent=2)
    return len(proxies)

def build_sub(cfgs, title, path):
    cnt = Counter(); lines = []
    for e in cfgs:
        cnt[e['cc']] += 1
        name = CC.get(e['cc'], e['cc'] or "Anycast")
        tag = "⚪БС" if e["wl"] else "•"
        lines.append(e["uri"].split("#",1)[0] + "#" + up.quote(f"{flag(e['cc'])} {name} {tag}-{cnt[e['cc']]}"))
    hdr = [f"# profile-title: {title}","# profile-update-interval: 12",f"# Count: {len(lines)}",
           "# Stable: pick fastest on connect, hold whole session.",""]
    open(path,"w").write("\n".join(hdr)+"\n".join(lines)+"\n")
    open(path.replace(".txt","-base64.txt"),"w").write(
        base64.b64encode(("\n".join(lines)+"\n").encode()).decode()+"\n")

for cfgs, remarks, jpath, tpath in [
    (WL,   "ROOT VPN | Белые списки",        "root-vpn.json",         "root-vpn.txt"),
    (NORM, "ROOT VPN | Обычные",             "root-vpn-normal.json",  "root-vpn-normal.txt"),
    (PREM, "ROOT VPN | Премиум (US+CA)",     "root-vpn-premium.json", "root-vpn-premium.txt"),
    (ALL,  "ROOT VPN | Всё (Белые+Обычные)", "root-vpn-all.json",     "root-vpn-all.txt"),
]:
    n = build_json(cfgs, remarks, jpath)
    build_sub(cfgs, remarks, tpath)
    print(f"{remarks:28s} -> {jpath} ({n} servers) | countries: {len(set(e['cc'] for e in cfgs))}"
          f" | wl={sum(e['wl'] for e in cfgs)} normal={sum(not e['wl'] for e in cfgs)}")
