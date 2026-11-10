"""學術資料庫檢索：OpenAlex、Semantic Scholar、arXiv。結果存成 JSON 並印出精簡列表。"""
import json, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
UA = {"User-Agent": "ssc-pinns-literature-review/0.1"}
OUT = sys.argv[1]

QUERIES = [
    "physics-informed neural network suspended sediment concentration",
    "physics-informed neural network sediment transport river",
    "physics-informed neural network sediment transport two-dimensional shallow water",
    "physics-informed neural network advection diffusion inverse parameter estimation river",
    "physics-informed neural network settling velocity sediment",
    "physics-informed neural network reservoir sedimentation",
    "physics-informed neural network turbidity",
    "physics-informed neural network water quality transport river inverse",
    "physics-informed neural network depth-averaged transport numerical model velocity field",
    "PINN dispersion coefficient estimation river field data",
]

def get(url, tries=3):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.read()
        except Exception as e:
            err = e; time.sleep(3 * (k + 1))
    print("  ! 失敗", url[:90], err); return None

res = {}
for q in QUERIES:
    res[q] = {"openalex": [], "s2": [], "arxiv": []}
    b = get("https://api.openalex.org/works?per-page=25&search=" + urllib.parse.quote(q))
    if b:
        for w in json.loads(b).get("results", []):
            src = (w.get("primary_location") or {}).get("source") or {}
            res[q]["openalex"].append({"title": w.get("title"), "year": w.get("publication_year"),
                                       "venue": src.get("display_name"), "doi": w.get("doi"),
                                       "cited": w.get("cited_by_count"), "type": w.get("type")})
    time.sleep(1)
    b = get("https://api.semanticscholar.org/graph/v1/paper/search?limit=25&fields=title,year,venue,externalIds,citationCount,publicationTypes&query=" + urllib.parse.quote(q))
    if b:
        for p in json.loads(b).get("data", []):
            res[q]["s2"].append({"title": p.get("title"), "year": p.get("year"), "venue": p.get("venue"),
                                 "doi": (p.get("externalIds") or {}).get("DOI"), "cited": p.get("citationCount")})
    time.sleep(3)
    b = get("http://export.arxiv.org/api/query?max_results=15&search_query=" + urllib.parse.quote("all:" + q.replace(" ", " AND all:")))
    if b:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for e in ET.fromstring(b).findall("a:entry", ns):
            res[q]["arxiv"].append({"title": " ".join(e.find("a:title", ns).text.split()),
                                    "year": e.find("a:published", ns).text[:4], "id": e.find("a:id", ns).text})
    time.sleep(3)

json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
seen = {}
for q, d in res.items():
    for src, items in d.items():
        for it in items:
            t = (it.get("title") or "").strip()
            k = t.lower()[:80]
            if not t or k in seen: continue
            seen[k] = 1
            print(f"[{src}] {it.get('year')} | {t[:150]} | {it.get('venue') or ''} | {it.get('doi') or it.get('id') or ''} | cited={it.get('cited')}")
print("共", len(seen), "篇（去重）")
