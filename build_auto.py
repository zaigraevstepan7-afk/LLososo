#!/usr/bin/env python3
"""Build a 100-server Yandex-SNI set: subscription + auto-balancer Xray JSON (leastPing)."""
import re, base64, glob, json, urllib.parse as up, datetime
from collections import Counter

WANT = 100
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
 "AT":"Austria","ES":"Spain","KZ":"Kazakhstan","RS":"Serbia"}
SKIP = {"RU","EU","AQ","UN"}
def flag(cc): return "".join(chr(0x1F1E6+ord(c)-65) for c in cc) if cc else "🌐"

def parse(u):
    rest = u.split("://",1)[1]; frag=""
    if "#" in rest: rest, frag = rest.split("#",1); frag = up.unquote(frag)
    userinfo_host = rest.split("?",1)[0]
    uid, _, host = userinfo_host.partition("@")
    q = rest.split("?",1)[1] if "?" in rest else ""
    return uid, host, dict(up.parse_qsl(q)), frag

cfgs, seen = [], set()
for f in glob.glob("yx/*.raw"):
    for m in URI.findall(norm(open(f, encoding="utf-8", errors="ignore").read())):
        u = m.strip().rstrip(",").replace("&amp;", "&")
        try: uid, host, par, frag = parse(u)
        except Exception: continue
        if ":" not in host: continue
        sni = (par.get("sni") or par.get("serverName","")).lower()
        if "yandex" not in sni: continue
        if par.get("security") != "reality": continue
        if (par.get("type") or "tcp") != "tcp": continue          # JSON template is TCP-reality
        cc = f2cc(frag)
        if cc in SKIP: continue
        addr, _, port = host.rpartition(":")
        if not port.isdigit(): continue
        key = (addr, port, par.get("pbk",""))
        if key in seen: continue
        seen.add(key)
        score = (10 if sni == "storage.yandex.net" else 0) + (3 if par.get("flow","").startswith("xtls-rprx-vision") else 0) + (2 if cc else 0)
        cfgs.append({"uri":u,"uid":uid,"addr":addr,"port":int(port),"sni":sni,"cc":cc,
                     "flow":par.get("flow",""),"pbk":par.get("pbk",""),"sid":par.get("sid",""),
                     "fp":par.get("fp","chrome"),"score":score})

cfgs.sort(key=lambda e: -e["score"])
cfgs = cfgs[:WANT]
print(f"Collected {len(cfgs)} Yandex-SNI TCP-Reality servers")
print("countries:", dict(Counter(e['cc'] or '??' for e in cfgs)))
print("SNI:", dict(Counter(e['sni'] for e in cfgs)))

# ---------- 1) subscription file ----------
cnt = Counter(); sub = []
for e in cfgs:
    cnt[e['cc']] += 1
    name = CC.get(e['cc'], e['cc'] or "Anycast")
    label = f"{flag(e['cc'])} {name} ⚪Я-{cnt[e['cc']]}"
    sub.append(e["uri"].split("#",1)[0] + "#" + up.quote(label))
date = datetime.datetime.utcnow().strftime("%Y-%m-%d / %H:%M (UTC)")
hdr = ["# profile-title: ROOT VPN",
 "# profile-update-interval: 6", f"# Date/Time: {date}", f"# Count: {len(sub)}",
 "# All non-RU servers, SNI=yandex. Enable URL-test/auto in your client to pick the fastest.",""]
open("root-vpn.txt","w").write("\n".join(hdr)+"\n".join(sub)+"\n")
open("root-vpn-base64.txt","w").write(base64.b64encode(("\n".join(sub)+"\n").encode()).decode()+"\n")

# ---------- 2) auto-balancer Xray JSON ----------
RU_DIRECT = ["domain:ru","domain:xn--p1ai","geosite:category-ru","domain:yandex","domain:vk.com",
 "domain:userapi.com","domain:vk-portal.net","domain:mail.ru","domain:ozon.ru","domain:wildberries.ru",
 "domain:avito.ru","domain:kinopoisk.ru","domain:gosuslugi.ru","domain:sberbank.ru","domain:tinkoff.ru",
 "domain:gismeteo.com","domain:2gis.com","domain:rutube.ru","domain:max.ru","domain:yastatic.net",
 "domain:yandexcloud.net","domain:mos.ru"]

def outbound(e, i):
    return {
        "mux": {"concurrency": -1, "enabled": False},
        "protocol": "vless",
        "settings": {"vnext": [{"address": e["addr"], "port": e["port"],
            "users": [{"encryption": "none", "flow": e["flow"], "id": e["uid"], "level": 8}]}]},
        "streamSettings": {
            "network": "tcp",
            "security": "reality",
            "realitySettings": {"allowInsecure": False, "fingerprint": e["fp"] or "chrome",
                "publicKey": e["pbk"], "serverName": "storage.yandex.net" if e["sni"]=="storage.yandex.net" else e["sni"],
                "shortId": e["sid"], "show": False},
            "tcpSettings": {"header": {"type": "none"}},
        },
        "tag": f"proxy-{i+1}",
    }

proxies = [outbound(e, i) for i, e in enumerate(cfgs)]
config = {
    "dns": {"servers": ["https://8.8.8.8/dns-query","https://8.8.4.4/dns-query"], "queryStrategy": "UseIP"},
    "inbounds": [
        {"listen":"127.0.0.1","port":10808,"protocol":"socks",
         "settings":{"auth":"noauth","udp":True,"userLevel":8},
         "sniffing":{"destOverride":["http","tls"],"enabled":True,"routeOnly":False},"tag":"socks"},
        {"listen":"127.0.0.1","port":10809,"protocol":"http","settings":{"userLevel":8},"tag":"http"},
    ],
    "log": {"loglevel": "warning"},
    "outbounds": proxies + [
        {"protocol":"freedom","settings":{"domainStrategy":"UseIP"},"tag":"direct"},
        {"protocol":"blackhole","settings":{"response":{"type":"http"}},"tag":"block"},
    ],
    "remarks": "ROOT VPN",
    "routing": {
        "domainStrategy":"IPIfNonMatch","domainMatcher":"hybrid",
        "rules":[
            {"type":"field","protocol":["bittorrent"],"outboundTag":"direct"},
            {"type":"field","outboundTag":"direct","domain":RU_DIRECT},
            {"type":"field","network":"tcp,udp","balancerTag":"auto"},
        ],
        "balancers":[{"tag":"auto","selector":["proxy-"],
            "strategy":{"type":"leastPing"},"fallbackTag":"proxy-1"}],
    },
    # STABLE MODE: probe once at connect, then freeze. Re-pick only on reconnect (core restart).
    "observatory": {
        "subjectSelector":["proxy-"],
        "probeURL":"https://www.gstatic.com/generate_204",
        "probeInterval":"9000h","enableConcurrency":True,
    },
}
# mux off + keep-alive on every proxy => stable held connection, good for gaming
for _o in config["outbounds"]:
    if _o.get("protocol") == "vless":
        _o["mux"] = {"enabled": False, "concurrency": -1}
        _o["streamSettings"]["sockopt"] = {"tcpKeepAliveInterval":15,"tcpKeepAliveIdle":30,"tcpMptcp":False}
open("root-vpn.json","w").write(json.dumps(config, ensure_ascii=False, indent=2))
print("Wrote root-vpn.json (outbounds:", len(proxies), ")")
print("Wrote root-vpn.txt / -base64.txt")
