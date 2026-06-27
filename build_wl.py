#!/usr/bin/env python3
"""Build a WHITE-LIST VLESS Reality subscription: non-RU servers, RU-whitelist SNI (DPI-bypass)."""
import glob, re, urllib.parse as up
from collections import defaultdict, Counter

WANT = 30
URI_RE = re.compile(r"(?:vless|hysteria2|hy2)://[^\s'\"<>]+")

def flag_to_cc(frag):
    ris = [ord(c) - 0x1F1E6 for c in frag if 0x1F1E6 <= ord(c) <= 0x1F1FF]
    return (chr(65+ris[0])+chr(65+ris[1])) if len(ris) >= 2 else None

CC_NAME = {"DE":"Germany","NL":"Netherlands","FR":"France","FI":"Finland","SE":"Sweden",
 "US":"United States","JP":"Japan","SG":"Singapore","KR":"South Korea","IN":"India","BR":"Brazil",
 "EE":"Estonia","LV":"Latvia","PL":"Poland","TR":"Turkey","GB":"United Kingdom","CA":"Canada",
 "CH":"Switzerland","HK":"Hong Kong","TW":"Taiwan","LT":"Lithuania","AT":"Austria","ES":"Spain",
 "IT":"Italy","RO":"Romania","UA":"Ukraine","KZ":"Kazakhstan","AE":"UAE","CN":"China","CZ":"Czechia",
 "HU":"Hungary","SI":"Slovenia","IL":"Israel","SC":"Seychelles","NO":"Norway","DK":"Denmark",
 "IE":"Ireland","BE":"Belgium","BG":"Bulgaria","GR":"Greece","PT":"Portugal","RS":"Serbia",
 "SK":"Slovakia","HR":"Croatia","AU":"Australia","CY":"Cyprus","MD":"Moldova","AM":"Armenia",
 "GE":"Georgia","LU":"Luxembourg","IS":"Iceland","RU":"Russia"}
SKIP_CC = {"RU","EU","AQ","UN"}
def cc_flag(cc): return "".join(chr(0x1F1E6+ord(c)-65) for c in cc)

# Russian "white list" SNIs that DPI does NOT throttle (same idea as user's working storage.yandex.net)
RU_WHITELIST_HINTS = ("yandex","ozon","ozone.ru","vk.com","vk.ru","id.vk","mail.ru",
 "kinopoisk","avito","pervye.ru","genproc.gov.ru","gosuslugi","sberbank","sber.ru",
 "x5.ru","rbc.ru","gismeteo","2gis","rutube","tinkoff","tbank","wildberries","mos.ru",
 "rt.ru","mts.ru","beeline","megafon","kontur","ngenix.net")

def sni_score(sni):
    s = sni.lower()
    if "yandex" in s: return 100          # user CONFIRMED yandex works -> top priority
    if any(h in s for h in RU_WHITELIST_HINTS): return 80   # other RU whitelist domains
    if s.endswith(".ru"): return 60       # any .ru domain = likely whitelisted
    if any(h in s for h in ("microsoft","mozilla","github","google","cloudflare","amd.com","zoom","webex")):
        return 30                          # global CDNs, usually pass
    return 5

def parse(uri):
    proto, rest = uri.split("://",1)
    frag = ""
    if "#" in rest: rest, frag = rest.split("#",1); frag = up.unquote(frag)
    netloc = rest.split("?",1)[0]; host = netloc.split("@",1)[-1]
    query = rest.split("?",1)[1] if "?" in rest else ""
    return proto, host, dict(up.parse_qsl(query)), frag

entries, seen = [], set()
for path in sorted(glob.glob("wl/*.txt")+glob.glob("wl/*.raw")):
    text = open(path, encoding="utf-8", errors="ignore").read()
    for m in URI_RE.findall(text):
        uri = m.strip().rstrip(",").replace("&amp;","&")
        try: proto, host, params, frag = parse(uri)
        except Exception: continue
        if ":" not in host: continue
        cc = flag_to_cc(frag)
        if not cc or cc in SKIP_CC: continue          # must be non-RU server with known flag
        if params.get("security") != "reality": continue  # white-list = Reality only
        sni = params.get("sni") or params.get("serverName","")
        if not sni: continue
        key = (host, params.get("pbk",""))
        if key in seen: continue
        seen.add(key)
        score = sni_score(sni)
        if params.get("flow","").startswith("xtls-rprx-vision"): score += 3
        entries.append({"uri":uri,"host":host,"cc":cc,"sni":sni,"score":score})

print(f"Reality white-list candidates (non-RU server): {len(entries)}")
print("SNI tiers:", Counter('yandex' if 'yandex' in e['sni'] else
      ('.ru/RU-wl' if (e['sni'].lower().endswith('.ru') or any(h in e['sni'].lower() for h in RU_WHITELIST_HINTS)) else 'other')
      for e in entries))

# select: highest SNI score first, then spread across countries
entries.sort(key=lambda e: -e["score"])
by_cc = defaultdict(list)
for e in entries: by_cc[e["cc"]].append(e)
order = sorted(by_cc, key=lambda c: -by_cc[c][0]["score"])

selected = []
# pass 1: country diversity (best config per country)
for c in order:
    if len(selected) >= WANT: break
    selected.append(by_cc[c].pop(0))
# pass 2: fill remaining slots with next-best globally (still no dup host)
rest = sorted((e for lst in by_cc.values() for e in lst), key=lambda e: -e["score"])
for e in rest:
    if len(selected) >= WANT: break
    selected.append(e)

counts = defaultdict(int); out = []
for e in sorted(selected, key=lambda e: (-e["score"], e["cc"])):
    counts[e["cc"]] += 1
    name = CC_NAME.get(e["cc"], e["cc"])
    tag = "⚪БС" if (e['sni'].lower().endswith('.ru') or 'yandex' in e['sni'].lower()
                    or any(h in e['sni'].lower() for h in RU_WHITELIST_HINTS)) else "•"
    label = f"{cc_flag(e['cc'])} {name} {tag}-{counts[e['cc']]} [{e['sni']}]"
    out.append(e["uri"].split("#",1)[0] + "#" + up.quote(label))

print(f"\nSelected {len(out)} across {len(set(e['cc'] for e in selected))} countries")
print("By country:", dict(Counter(e['cc'] for e in selected)))
print("SNI used:", dict(Counter(e['sni'] for e in selected)))
open("wl_selected.txt","w").write("\n".join(out)+"\n")
