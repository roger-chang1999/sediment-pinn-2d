"""第二輪：OpenAlex 標題摘要過濾＋被引用追蹤；Semantic Scholar 放慢重試。"""
import json, sys, time, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
UA = {"User-Agent": "ssc-pinns-literature-review/0.1"}
OUT = sys.argv[1]

def get(url, tries=4, wait=5):
    err = None
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return json.loads(r.read())
        except Exception as e:
            err = e; time.sleep(wait * (k + 1))
    print("  ! 失敗", url[:100], err); return None

def oa_rows(d, tag):
    rows = []
    for w in (d or {}).get("results", []):
        src = (w.get("primary_location") or {}).get("source") or {}
        rows.append({"via": tag, "title": w.get("title"), "year": w.get("publication_year"),
                     "venue": src.get("display_name"), "doi": w.get("doi"), "cited": w.get("cited_by_count"), "id": w.get("id")})
    return rows

rows = []
# 1) 標題＋摘要過濾（較精準）
for term in ["physics-informed sediment", "physics-informed suspended", "physics-informed turbidity",
             "PINN sediment", "PINN suspended", "physics-informed advection-dispersion river",
             "physics-informed neural network sediment concentration inverse"]:
    flt = "title_and_abstract.search:" + term
    d = get("https://api.openalex.org/works?per-page=50&sort=cited_by_count:desc&filter=" + urllib.parse.quote(flt))
    rows += oa_rows(d, "oa-filter:" + term); time.sleep(1)

# 2) 被引用追蹤（forward citation）：先用 DOI 找 OpenAlex ID
seeds = {"PINN-Sed": "10.1061/jhend8.hyeng-14926", "Delcey2024": "10.1016/j.cma.2024.117389",
         "He2021-ADE-WRR": "10.1029/2020wr029479", "Ohara2024": "10.1063/5.0232852",
         "Niu2023": "10.1016/j.jhydrol.2023.130048", "Jhydrol2023-pollutant": "10.1016/j.jhydrol.2023.129354",
         "Fanous2025": "10.1016/j.ecoinf.2025.103302"}
for name, doi in seeds.items():
    w = get("https://api.openalex.org/works/doi:" + doi)
    if not w: continue
    wid = w["id"].rsplit("/", 1)[-1]
    print(f"  seed {name}: {wid} cited_by={w.get('cited_by_count')}")
    d = get(f"https://api.openalex.org/works?per-page=100&filter=cites:{wid}")
    rows += oa_rows(d, "cites:" + name); time.sleep(1)

# 3) Semantic Scholar 放慢重試
for q in ["physics-informed neural network suspended sediment", "physics-informed neural network sediment transport",
          "physics-informed neural network advection dispersion inverse river"]:
    time.sleep(12)
    d = get("https://api.semanticscholar.org/graph/v1/paper/search?limit=40&fields=title,year,venue,externalIds,citationCount&query=" + urllib.parse.quote(q), tries=4, wait=15)
    for p in (d or {}).get("data", []):
        rows.append({"via": "s2:" + q, "title": p.get("title"), "year": p.get("year"), "venue": p.get("venue"),
                     "doi": (p.get("externalIds") or {}).get("DOI"), "cited": p.get("citationCount")})

json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
seen = {}
for r in rows:
    t = (r.get("title") or "").strip(); k = t.lower()[:80]
    if not t: continue
    seen.setdefault(k, []).append(r["via"])
    if len(seen[k]) == 1:
        print(f"{r.get('year')} | {t[:140]} | {r.get('venue') or ''} | {r.get('doi') or ''} | cited={r.get('cited')} | {r['via']}")
print("共", len(seen), "篇（去重）")
