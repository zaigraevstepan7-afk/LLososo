import re, urllib.parse
from collections import defaultdict

configs = []  # (latency, country, host, raw_line)

def parse_10ium(path):
    out=[]
    for line in open(path, encoding='utf-8'):
        line=line.strip()
        if not line.startswith('vless://'): continue
        m=re.search(r'#REALITY\|([A-Z]{2}).*?\|\s*[\d\.]+ms', line)
        lat=re.search(r'\|\s*([\d\.]+)ms', line)
        if not m or not lat: continue
        cc=m.group(1); latency=float(lat.group(1))
        host=re.search(r'@([^:?#]+)', line)
        host=host.group(1) if host else line
        out.append((latency, cc, host, line))
    return out

raw = parse_10ium('vpn_sources/10ium_reality.txt')
print("parsed reality configs:", len(raw))

# exclude Russia
raw = [c for c in raw if c[1] != 'RU']
print("after excluding RU:", len(raw))

# dedupe by host, keep lowest latency
best_by_host={}
for lat,cc,host,line in raw:
    if host not in best_by_host or lat < best_by_host[host][0]:
        best_by_host[host]=(lat,cc,host,line)
uniq=sorted(best_by_host.values(), key=lambda x:x[0])
print("unique hosts:", len(uniq))

# diversity: cap per country, then fill by latency
PER_COUNTRY_CAP=5
count=defaultdict(int)
selected=[]
for lat,cc,host,line in uniq:
    if len(selected)>=30: break
    if count[cc]>=PER_COUNTRY_CAP: continue
    count[cc]+=1
    selected.append((lat,cc,host,line))
# fill remaining if under 30
if len(selected)<30:
    chosen=set(id(x) for x in selected)
    for item in uniq:
        if len(selected)>=30: break
        if id(item) in chosen: continue
        selected.append(item)
selected=sorted(selected, key=lambda x:x[0])[:30]
print("selected:", len(selected))
print("country spread:", dict(sorted(((c, sum(1 for s in selected if s[1]==c)) for c in set(s[1] for s in selected)), key=lambda x:-x[1])))

# rename tags to clean flags + country + latency
FLAG={'DE':'🇩🇪','NL':'🇳🇱','US':'🇺🇸','FR':'🇫🇷','FI':'🇫🇮','SE':'🇸🇪','SC':'🇸🇨','TR':'🇹🇷','GB':'🇬🇧','JP':'🇯🇵','SG':'🇸🇬','PL':'🇵🇱','IT':'🇮🇹','IR':'🇮🇷','CZ':'🇨🇿','LT':'🇱🇹','CN':'🇨🇳','CH':'🇨🇭','AE':'🇦🇪','KZ':'🇰🇿','BY':'🇧🇾','AT':'🇦🇹','AL':'🇦🇱','LV':'🇱🇻','KG':'🇰🇬','IE':'🇮🇪','HR':'🇭🇷','BG':'🇧🇬','AU':'🇦🇺'}

lines=[]
for i,(lat,cc,host,line) in enumerate(selected,1):
    base=line.split('#')[0]
    flag=FLAG.get(cc,'🏳️')
    tag=f"{flag} {cc} | {lat:.0f}ms | #{i:02d}"
    lines.append(base + '#' + urllib.parse.quote(tag))

from datetime import datetime
header=[
 "# profile-title: 🌍 BEST VLESS REALITY | NO-RUSSIA | TOP-30",
 "# profile-update-interval: 1",
 f"# Date/Time: {datetime.utcnow().strftime('%Y-%m-%d / %H:%M')} (UTC)",
 f"# Количество: {len(lines)}",
 "# Источники: 10ium/V2Hub3, barry-far, igareck (отсортировано по пингу, RU исключена)",
 "",
]
out='\n'.join(header+lines)+'\n'
open('vless_best_top30_no_russia.txt','w',encoding='utf-8').write(out)

import base64
b64=base64.b64encode(out.encode()).decode()
open('vless_best_top30_no_russia_base64.txt','w').write(b64)
print("\nWritten files. base64 length:", len(b64))
print("\n=== preview ===")
print('\n'.join(out.splitlines()[:9]))
