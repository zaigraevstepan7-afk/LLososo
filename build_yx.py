#!/usr/bin/env python3
"""WHITE-LIST subscription using ONLY Yandex SNI (storage.yandex.net etc), non-RU servers."""
import re, base64, glob, urllib.parse as up, datetime
from collections import defaultdict, Counter
WANT=30
def norm(t):
    if "://" in t: return t
    c=re.sub(r"\s+","",t)
    try:
        d=base64.b64decode(c+"="*(-len(c)%4)).decode("utf-8","ignore"); return d if "://" in d else t
    except: return t
URI=re.compile(r"(?:vless|hysteria2|hy2)://[^\s'\"<>]+")
def f2cc(fr):
    r=[ord(c)-0x1F1E6 for c in fr if 0x1F1E6<=ord(c)<=0x1F1FF]
    return (chr(65+r[0])+chr(65+r[1])) if len(r)>=2 else None
CC={"DE":"Germany","NL":"Netherlands","FR":"France","FI":"Finland","SE":"Sweden","US":"United States",
 "JP":"Japan","SG":"Singapore","KR":"South Korea","IN":"India","BR":"Brazil","EE":"Estonia","LV":"Latvia",
 "PL":"Poland","TR":"Turkey","GB":"United Kingdom","CA":"Canada","CH":"Switzerland","HK":"Hong Kong",
 "TW":"Taiwan","LT":"Lithuania","AT":"Austria","ES":"Spain","IT":"Italy","RO":"Romania","UA":"Ukraine",
 "KZ":"Kazakhstan","AE":"UAE","CN":"China","CZ":"Czechia","HU":"Hungary","SI":"Slovenia","IL":"Israel",
 "SC":"Seychelles","NO":"Norway","DK":"Denmark","IE":"Ireland","BE":"Belgium","BG":"Bulgaria","GR":"Greece",
 "PT":"Portugal","RS":"Serbia","SK":"Slovakia","HR":"Croatia","AU":"Australia","CY":"Cyprus","MD":"Moldova",
 "AM":"Armenia","GE":"Georgia","LU":"Luxembourg","IS":"Iceland"}
SKIP={"RU","EU","AQ","UN"}
def flag(cc): return "".join(chr(0x1F1E6+ord(c)-65) for c in cc)
def parse(u):
    p,rest=u.split("://",1); fr=""
    if "#" in rest: rest,fr=rest.split("#",1); fr=up.unquote(fr)
    host=rest.split("?",1)[0].split("@",1)[-1]
    q=rest.split("?",1)[1] if "?" in rest else ""
    return p,host,dict(up.parse_qsl(q)),fr
ent,seen=[],set()
for f in glob.glob("yx/*.raw"):
    for m in URI.findall(norm(open(f,encoding="utf-8",errors="ignore").read())):
        u=m.strip().rstrip(",").replace("&amp;","&")
        try: p,host,par,fr=parse(u)
        except: continue
        if ":" not in host: continue
        sni=(par.get("sni") or par.get("serverName","")).lower()
        if "yandex" not in sni: continue            # ONLY yandex SNI
        if par.get("security")!="reality": continue
        cc=f2cc(fr)
        if cc in SKIP: continue                      # drop RU-located / junk; keep unknown(None) too
        key=(host,par.get("pbk",""))
        if key in seen: continue
        seen.add(key)
        sc=0
        if sni=="storage.yandex.net": sc+=10         # exactly user's working decoy
        if par.get("flow","").startswith("xtls-rprx-vision"): sc+=3
        if cc: sc+=2
        ent.append({"uri":u,"host":host,"cc":cc,"sni":sni,"score":sc})
print("Yandex-SNI Reality candidates (non-RU):",len(ent))
ent.sort(key=lambda e:-e["score"])
# country diversity first, then fill
by=defaultdict(list)
for e in ent: by[e["cc"] or "??"].append(e)
order=sorted(by,key=lambda c:-by[c][0]["score"])
sel=[]
for c in order:
    if len(sel)>=WANT: break
    if c!="??": sel.append(by[c].pop(0))
rest=sorted((e for l in by.values() for e in l),key=lambda e:-e["score"])
for e in rest:
    if len(sel)>=WANT: break
    sel.append(e)
cnt=defaultdict(int); out=[]
for e in sorted(sel,key=lambda e:(-e["score"], e["cc"] or "ZZ")):
    cc=e["cc"]; cnt[cc]+=1
    name=CC.get(cc,cc) if cc else "Anycast"
    fl=flag(cc) if cc else "🌐"
    out.append(e["uri"].split("#",1)[0]+"#"+up.quote(f"{fl} {name} ⚪Яндекс-{cnt[cc]} [{e['sni']}]"))
print("Selected",len(out),"| countries:",dict(Counter(e['cc'] for e in sel)))
print("SNI:",dict(Counter(e['sni'] for e in sel)))
date=datetime.datetime.utcnow().strftime("%Y-%m-%d / %H:%M (UTC)")
hdr=["# profile-title: 🟡 ЯНДЕКС | VLESS Reality (SNI=yandex) | DPI-bypass",
 "# profile-update-interval: 6", f"# Date/Time: {date}", f"# Count: {len(out)}",
 "# All servers OUTSIDE Russia, SNI masquerades as Yandex (storage.yandex.net) - same as Liberty VPN.",""]
open("Yandex-SNI-VLESS-Reality-NoRU.txt","w").write("\n".join(hdr)+"\n".join(out)+"\n")
open("Yandex-SNI-VLESS-Reality-NoRU-base64.txt","w").write(base64.b64encode(("\n".join(out)+"\n").encode()).decode()+"\n")
