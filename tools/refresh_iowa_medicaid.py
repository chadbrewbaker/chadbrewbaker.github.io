#!/usr/bin/env python3
"""refresh_iowa_medicaid.py — snapshot Iowa Medicaid data for the browser tool.

Downloads from the Iowa Data Hub (data.iowa.gov, post-2025 migration):
  dataset 974: Payments & Recipients by Month and Category of Service
  dataset 973: Payments & Recipients by Month and County
and writes a compact iowa_medicaid_data.json next to iowa-medicaid.html.

Stdlib only. Run:  python3 refresh_iowa_medicaid.py
License of the data: CC BY 4.0, State of Iowa HHS Division of Medicaid.

The hub API (idh-be.iowa.gov/api/v1/datasets/{id}/rows.{csv,json}) has been
observed to serve zip-wrapped payloads; this script sniffs and handles
plain CSV, plain JSON, or a zip containing either. Column names are
normalized and matched by substring, so modest schema drift survives.

Also prints a reconciliation report, including the question that decides
what the category chart can honestly claim: whether MCO capitation is a
category line (state pays plans; categories are the capitation buckets)
or absent (categories are FFS/encounter-based detail).
"""
import csv, io, json, re, sys, urllib.request, zipfile
from collections import defaultdict
from datetime import date

HUB = "https://idh-be.iowa.gov/api/v1/datasets/{id}/rows.{fmt}"
CKAN = "https://catalog.data.gov/api/3/action/package_search?q="
UA = {"User-Agent": "iowa-medicaid-browser/1.0 (public data snapshot script)"}

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()

def rows_from_bytes(raw):
    """plain CSV | plain JSON | zip containing either -> list of dicts"""
    if raw[:2] == b"PK":
        zf = zipfile.ZipFile(io.BytesIO(raw))
        names = zf.namelist()
        inner = sorted(names, key=lambda n: (not n.endswith((".csv", ".json")), n))[0]
        raw = zf.read(inner)
    text = raw.decode("utf-8-sig", errors="replace").strip()
    if text[:1] in "[{":
        data = json.loads(text)
        if isinstance(data, dict):           # {"rows":[...]} / {"data":[...]} shapes
            for k in ("rows", "data", "results", "items"):
                if isinstance(data.get(k), list):
                    data = data[k]
                    break
        if data and isinstance(data[0], list) and isinstance(data, list):
            # array-of-arrays with a header row
            hdr = [str(h) for h in data[0]]
            return [dict(zip(hdr, r)) for r in data[1:]]
        return list(data)
    return list(csv.DictReader(io.StringIO(text)))

def norm(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_")

def pick(cols, *needles, exclude=()):
    for c in cols:
        n = norm(c)
        if any(x in n for x in needles) and not any(x in n for x in exclude):
            return c
    return None

def pick_pref(cols, preferred, needles, exclude=()):
    # exact (normalized) name first, substring fallback
    by_norm = {norm(c): c for c in cols}
    for p in preferred:
        if norm(p) in by_norm:
            return by_norm[norm(p)]
    return pick(cols, *needles, exclude=exclude)

MONTH_PATTERNS = [
    (re.compile(r"^(\d{4})-(\d{2})"), lambda m: (int(m[1]), int(m[2]))),
    (re.compile(r"^(\d{1,2})/\d{1,2}/(\d{4})"), lambda m: (int(m[2]), int(m[1]))),
]
def month_of(v):
    v = str(v).strip()
    for rx, f in MONTH_PATTERNS:
        m = rx.match(v)
        if m:
            y, mo = f(m)
            return "%04d-%02d" % (y, mo)
    return None

def money(v):
    if v in (None, ""):
        return 0.0
    return float(re.sub(r"[$,\s]", "", str(v)) or 0)

def process(rows, dim_needles, dim_exclude=(), prefs=None):
    """-> (months sorted, {dim_value: {month: {payments, recipients, ...}}}, colmap)"""
    prefs = prefs or {}
    cols = list(rows[0].keys())
    c_date = pick_pref(cols, prefs.get("date", ()), ("report_date", "date", "month_ending", "month"))
    c_dim  = pick_pref(cols, prefs.get("dim", ()), dim_needles, dim_exclude)
    c_pay  = pick_pref(cols, prefs.get("payments", ()), ("payment", "pmt", "amount", "paid"),
                       exclude=("med_needy", "other_"))
    c_rec  = pick_pref(cols, prefs.get("recipients", ()), ("recipients_served", "recip", "served"),
                       exclude=("eligible", "elig", "med_needy", "other_"))
    c_eli  = pick_pref(cols, prefs.get("eligibles", ()), ("eligible", "elig"),
                       exclude=("med_needy", "other_", "avg", "cost", "per_", "pct", "rate"))
    c_clm  = pick(cols, "claim")
    c_unit = pick(cols, "unit")
    if not (c_date and c_dim and c_pay):
        raise RuntimeError("could not identify columns; got: %s" % cols)
    out = defaultdict(dict)
    months = set()
    dropped_dims = set()
    total_rx = re.compile(r"^(grand\s+)?total|statewide|^state$", re.I)
    for r in rows:
        m = month_of(r.get(c_date, ""))
        if not m:
            continue
        d = str(r.get(c_dim, "")).strip() or "(unlabeled)"
        if prefs.get("drop_totals") and total_rx.search(d):
            dropped_dims.add(d)
            continue
        months.add(m)
        cell = out[d].setdefault(m, defaultdict(float))
        cell["payments"] += money(r.get(c_pay))
        if c_rec:  cell["recipients"] += money(r.get(c_rec))
        if c_eli:  cell["eligibles"]  += money(r.get(c_eli))
        if c_clm:  cell["claims"]     += money(r.get(c_clm))
        if c_unit: cell["units"]      += money(r.get(c_unit))
    if dropped_dims:
        print("  dropped total-style rows to avoid double counting:", sorted(dropped_dims))
    colmap = {"date": c_date, "dim": c_dim, "payments": c_pay,
              "recipients": c_rec, "eligibles": c_eli, "claims": c_clm, "units": c_unit}
    return sorted(months), dict(out), colmap

def pack(months, table, fields):
    series = {}
    for dim, by_m in sorted(table.items()):
        entry = {}
        for f in fields:
            vals = [round(by_m.get(m, {}).get(f, 0.0), 2) for m in months]
            if any(vals):
                entry[f] = vals
        series[dim] = entry
    return series

def discover_hub_url(title_query):
    """Resolve a dataset's current idh-be download URL by title via data.gov CKAN.
    Robust to the Iowa portal's ID churn (which has already happened once)."""
    import urllib.parse
    url = CKAN + urllib.parse.quote('title:"%s"' % title_query)
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            res = json.loads(r.read().decode())
    except Exception as e:
        print("  CKAN discovery failed for %r: %s" % (title_query, e), file=sys.stderr)
        return None
    for pkg in res.get("result", {}).get("results", []):
        for rsc in pkg.get("resources", []):
            u = rsc.get("url", "")
            if "idh-be.iowa.gov" in u and u.endswith((".csv", ".json")):
                print("  discovered %r -> %s" % (pkg.get("title"), u))
                return u
    print("  CKAN: no idh-be resource found for %r" % title_query, file=sys.stderr)
    return None

# The county budget dataset had NOT migrated to the Iowa Data Hub as of July 2026
# (data.gov still references its legacy Socrata identity). Fallback chain:
# hub (via CKAN discovery) -> legacy Socrata endpoint -> loud failure on stdout.
COUNTY_BUDGET_URL = "https://idh-be.iowa.gov/api/v1/datasets/939/rows.csv"   # hub id 939 (verified July 2026)
COUNTY_BUDGET_SOCRATA = "https://data.iowa.gov/resource/gk9s-gz9c.csv?$limit=500000"

def county_budget_section():
    """All-counties budgeted expenditures by service area (FY2005+).
    Mental-health / county-hospital service areas are the levy-side context for
    the Medicaid picture."""
    rows = None
    url = COUNTY_BUDGET_URL
    try:
        rows = rows_from_bytes(fetch(url))
    except Exception as e:
        print("  county budget: hub id 939 failed (%s), trying CKAN discovery" % e)
        url = discover_hub_url("County Budgeted Expenditures By Service Area")
    if rows is None and url:
        try:
            rows = rows_from_bytes(fetch(url))
        except Exception as e:
            print("  county budget: hub download failed (%s), trying legacy Socrata" % e)
    if rows is None:
        url = COUNTY_BUDGET_SOCRATA
        try:
            rows = rows_from_bytes(fetch(url))
            print("  county budget: served by legacy Socrata endpoint (pre-migration)")
        except Exception as e:
            print("COUNTY BUDGET UNAVAILABLE: hub discovery found nothing and Socrata fallback")
            print("failed (%s)." % e)
            print("Manual fix: find 'County Budgeted Expenditures By Service Area' on")
            print("data.iowa.gov, copy its CSV download URL, and set COUNTY_BUDGET_SOCRATA.")
            return None
    cols = list(rows[0].keys())
    c_fy   = pick(cols, "fiscal_year", "fy", "year", exclude=("end_date", "date"))
    c_cnty = pick(cols, "county_name", "county", exclude=("code", "fips"))
    c_area = pick(cols, "service_area", "service_class")
    c_amt  = pick(cols, "budgeted_expenditure", "amount") if c_area else None
    wide_areas = None
    if not c_area:
        # WIDE format (hub id 939): service areas are columns, one row per county-FY
        meta_rx = re.compile(r"total|sub_total|transfer|escrow|reserve|balance|requirement|"
                             r"code|_id|id_|^unique|date|year|county|fips", re.I)
        wide_areas = [c for c in cols if not meta_rx.search(norm(c))]
        by_norm = {norm(c): c for c in cols}
        if "total_expenditures" in by_norm:
            wide_areas.append(by_norm["total_expenditures"])
    if not (c_fy and c_cnty and (wide_areas or (c_area and c_amt))):
        print("  county budget: could not identify columns; got %s" % cols)
        return None
    print("  county-budget columns:", {"fy": c_fy, "county": c_cnty,
          "areas": wide_areas or [c_area], "format": "wide" if wide_areas else "long"})
    by_cnty = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))  # county->area->fy
    state = defaultdict(lambda: defaultdict(float))
    for r in rows:
        fy = re.sub(r"\D", "", str(r.get(c_fy, "")))[:4]
        if not fy:
            continue
        cnty = str(r.get(c_cnty, "")).strip().upper() or "(none)"
        if wide_areas:
            for a in wide_areas:
                amt = money(r.get(a))
                state[a][fy] += amt
                by_cnty[cnty][a][fy] += amt
        else:
            area = str(r.get(c_area, "")).strip() or "(none)"
            amt = money(r.get(c_amt))
            state[area][fy] += amt
            by_cnty[cnty][area][fy] += amt
    fys = sorted({fy for a in state.values() for fy in a})
    return {"fiscal_years": fys,
            "counties": {c: {a: [round(by_cnty[c][a].get(fy, 0.0), 2) for fy in fys]
                             for a in sorted(by_cnty[c])} for c in sorted(by_cnty)},
            "statewide": {a: [round(state[a].get(fy, 0.0), 2) for fy in fys] for a in sorted(state)},
            "source": url,
            "note": "budgeted (not actual) expenditures, all counties; FY = year ending June 30"}

CENSUS_KEY = __import__("os").environ.get("CENSUS_API_KEY", "")  # free: api.census.gov/data/key_signup.html
CENSUS_URLS = [
    ("https://api.census.gov/data/2023/acs/acs5?get=NAME,B01003_001E&for=county:*&in=state:19", "ACS 2023 5yr"),
    ("https://api.census.gov/data/2022/acs/acs5?get=NAME,B01003_001E&for=county:*&in=state:19", "ACS 2022 5yr"),
    ("https://api.census.gov/data/2020/dec/pl?get=NAME,P1_001N&for=county:*&in=state:19", "2020 Census PL"),
]

VENDOR_HUB = HUB.format(id=975, fmt="csv")   # confirmed July 2026: hub dataset 975 = medicaid_month_vendor
VENDOR_SOCRATA = "https://data.iowa.gov/resource/b3t9-awkp.csv?$limit=500000"
VENDOR_URL_OVERRIDE = None   # paste a working CSV URL here if both paths fail
VENDOR_LOCAL_FILE = None     # or path to a manually downloaded rows.csv (the 939 play)
ADAIR_PLACES = {"ADAIR", "GREENFIELD", "FONTANELLE", "ORIENT", "BRIDGEWATER"}

def vendor_section():
    """Facility-level LTC Medicaid payments (SNF/ICF/RCF/NFMI)."""
    rows = None; url = VENDOR_URL_OVERRIDE
    if VENDOR_LOCAL_FILE:
        try:
            rows = rows_from_bytes(open(VENDOR_LOCAL_FILE, "rb").read())
            url = "file://" + VENDOR_LOCAL_FILE
            print("  vendors: loaded local file", VENDOR_LOCAL_FILE)
        except Exception as e:
            print("  vendors: local file failed (%s)" % e)
    if rows is None and url:
        try: rows = rows_from_bytes(fetch(url))
        except Exception as e: print("  vendors: override failed (%s)" % e)
    if rows is None:
        try:
            rows = rows_from_bytes(fetch(VENDOR_HUB)); url = VENDOR_HUB
            print("  vendors: served by hub dataset 975")
        except Exception as e:
            print("  vendors: hub 975 failed (%s), trying discovery" % e)
    if rows is None:
        u = discover_hub_url("Iowa Medicaid Payments & Recipients by Month and Vendor")
        if u:
            try: rows = rows_from_bytes(fetch(u)); url = u
            except Exception as e: print("  vendors: hub failed (%s)" % e)
    if rows is None:
        try:
            rows = rows_from_bytes(fetch(VENDOR_SOCRATA)); url = VENDOR_SOCRATA
            print("  vendors: served by legacy Socrata endpoint")
        except Exception as e:
            print("VENDOR DATA UNAVAILABLE (%s). Set VENDOR_URL_OVERRIDE." % e)
            return None
    cols = list(rows[0].keys())
    print("  vendor dataset FULL columns:", cols)
    c_date = pick(cols, "report_date", "date", "month")
    name_cols = [c for c in cols if re.search(r"name", c, re.IGNORECASE) and not re.search(r"number|_no$|_id$", c, re.IGNORECASE)]
    c_ven = name_cols[0] if name_cols else pick(cols, "vendor_name", "vendor", "provider_name", "facility_name")
    c_num = pick(cols, "vendor_number", "provider_number")
    if c_ven == c_num:
        print("  WARNING: only numeric vendor IDs available — names need a crosswalk; see full columns above")
    c_cnty = pick(cols, "county"); c_city = pick(cols, "city")
    c_type = pick(cols, "vendor_type", "facility_type", "category", "type")
    c_pay  = pick(cols, "payment", "pmt", "amount")
    if not (c_date and c_ven and c_pay):
        print("  vendors: could not identify columns; got %s" % cols); return None
    print("  vendor columns:", {"date": c_date, "vendor": c_ven, "county": c_cnty,
                                "city": c_city, "type": c_type, "payments": c_pay})
    monthly = defaultdict(lambda: defaultdict(float)); meta = {}; months = set()
    for r in rows:
        m = month_of(r.get(c_date, ""))
        if not m: continue
        v = str(r.get(c_ven, "")).strip()
        months.add(m); monthly[v][m] += money(r.get(c_pay))
        if v not in meta:
            meta[v] = {"county": str(r.get(c_cnty, "")).strip().upper() if c_cnty else "",
                       "city": str(r.get(c_city, "")).strip().upper() if c_city else "",
                       "type": str(r.get(c_type, "")).strip() if c_type else ""}
    months = sorted(months); last12 = months[-12:]
    roster = sorted(({"vendor": v, **meta[v],
                      "latest12": round(sum(monthly[v].get(m, 0) for m in last12), 2)}
                     for v in monthly), key=lambda x: -x["latest12"])
    def is_adair(v):
        mt = meta[v]
        return mt["county"] == "ADAIR" or mt["city"] in ADAIR_PLACES \
               or any(pl in v.upper() for pl in ADAIR_PLACES)
    keep = {v for v in monthly if is_adair(v)} | {r["vendor"] for r in roster[:20]}
    adair_names = sorted(v for v in keep if is_adair(v))
    print("  vendors: %d facilities; Adair-area matches: %s"
          % (len(roster), adair_names or "NONE - check roster manually"))
    return {"months": months,
            "series": {v: [round(monthly[v].get(m, 0), 2) for m in months] for v in keep},
            "adair_vendors": adair_names, "roster": roster, "source": url,
            "note": "LTC facility types only; verify adair_vendors against roster."}

def population_section():
    """County population (ACS 5-year, total population B01003) for per-capita math."""
    data = None; vintage = None
    for url, label in CENSUS_URLS:
        raw = b""
        try:
            raw = fetch(url + ("&key=" + CENSUS_KEY if CENSUS_KEY else ""))
            data = json.loads(raw.decode("utf-8")); vintage = label
            break
        except Exception as e:
            print("  population: %s failed (%s); response head: %r" % (label, e, raw[:120]))
    if data is None:
        print("  population: all Census endpoints failed — per-capita hidden")
        return None
    out = {}
    for row in data[1:]:
        name = row[0].upper().replace(" COUNTY, IOWA", "").strip()
        out[name] = int(row[1])
    print("  population: %d counties (%s); POLK=%s JOHNSON=%s"
          % (len(out), vintage, "{:,}".format(out.get("POLK", 0)), "{:,}".format(out.get("JOHNSON", 0))))
    return {"by_county": out, "source": "api.census.gov", "vintage": vintage}

def main():
    out = {"generated": date.today().isoformat(),
           "source": {"category": HUB.format(id=974, fmt="csv"),
                      "county": HUB.format(id=973, fmt="csv"),
                      "license": "CC BY 4.0 — State of Iowa HHS, Division of Medicaid",
                      "landing": ["https://data.iowa.gov/catalog/dataset/974",
                                   "https://data.iowa.gov/catalog/dataset/973"]},
           "synthetic": False}

    DATASETS = (
        ("category", 974, ("category", "service"), ("date",), {
            "date": ("report_date",), "dim": ("service_category_name",),
            "payments": ("total_payments",), "recipients": ("total_recipients",)}),
        ("county", 973, ("county",), ("date", "fips"), {
            "date": ("report_date",), "dim": ("county_name",),
            # B-1 structure: total Title XIX = medically needy + all other
            "payments": ("total_txix_pmt",), "recipients": ("total_txix_recip",),
            "eligibles": ("total_txix_elig",), "drop_totals": True}),
    )
    errors = []
    for key, ds_id, needles, excl, prefs in DATASETS:
        raw = None
        for fmt in ("csv", "json"):
            try:
                raw = fetch(HUB.format(id=ds_id, fmt=fmt))
                break
            except Exception as e:
                print("  fetch %s.%s failed: %s" % (ds_id, fmt, e), file=sys.stderr)
        if raw is None:
            errors.append("dataset %d: download failed" % ds_id)
            continue
        try:
            rows = rows_from_bytes(raw)
            months, table, colmap = process(rows, needles, excl, prefs)
        except Exception as e:
            errors.append("dataset %d: %s" % (ds_id, e))
            continue
        print("dataset %d: %d rows, %d %s values, %s .. %s" %
              (ds_id, len(rows), len(table), key, months[0], months[-1]))
        print("  columns used:", {k: v for k, v in colmap.items() if v})
        fields = ("payments", "recipients", "eligibles", "claims", "units")
        out[key] = {"months": months, "series": pack(months, table, fields)}

    if errors:
        print("\nWARNING — partial snapshot:", "; ".join(errors), file=sys.stderr)
    if "category" not in out:
        sys.exit("dataset 974 unavailable; nothing to write")

    import os
    with open("iowa_medicaid_data.json", "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print("\nwrote iowa_medicaid_data.json (%.1f KB) — snapshot safe; report follows"
          % (os.path.getsize("iowa_medicaid_data.json") / 1024))

    # ---- reconciliation & semantics report ----
    cat = out["category"]
    n_months = len(cat["months"])
    latest12 = list(range(max(0, n_months - 12), n_months))
    by_latest = sorted(cat["series"].items(),
                       key=lambda kv: -sum(kv[1].get("payments", [0]*n_months)[i] for i in latest12))
    print("\nall %d service categories, by latest-12-month payments:" % len(by_latest))
    for c, sser in by_latest:
        tot = sum(sser.get("payments", [0]*n_months)[i] for i in latest12)
        print("  ${:>14,.0f}  {}".format(tot, c))
    total_by_year = defaultdict(float)
    for c, s in cat["series"].items():
        for i, m in enumerate(cat["months"]):
            total_by_year[m[:4]] += s.get("payments", [0]*len(cat["months"]))[i]
    print("\ncalendar-year totals from dataset 974 (compare to CMS-64 / LSA):")
    for y in sorted(total_by_year):
        if y >= "2018":
            print("  {}: ${:>15,.0f}".format(y, total_by_year[y]))
    mco = [c for c in cat["series"] if re.search(r"mco|managed|capitat|amerih|total care|molina|amerigroup", c, re.I)]
    print("\nMCO/capitation category lines found:" if mco else
          "\nNO MCO/capitation category lines found — categories are likely FFS + encounter detail;")
    for c in mco:
        print("  -", c)
    if not mco:
        print("  the page must say 'service-level detail as reported by the state', not 'all Medicaid spending'.")
    cnty_total = defaultdict(float)
    cy = out.get("county", {"months": [], "series": {}})
    for c, s in cy["series"].items():
        for i, m in enumerate(cy["months"]):
            cnty_total[m[:4]] += s.get("payments", [0]*len(cy["months"]))[i]
    print("\ncounty-dataset year totals (should track 974 if same universe):")
    for y in sorted(cnty_total):
        if y >= "2018":
            d = total_by_year.get(y, 0)
            pct = (cnty_total[y] / d * 100) if d else 0
            print("  {}: ${:>15,.0f}  ({:.1f}% of 974)".format(y, cnty_total[y], pct))

    pop = population_section()
    if pop:
        out["population"] = pop
        with open("iowa_medicaid_data.json", "w") as f:
            json.dump(out, f, separators=(",", ":"))
    vs = vendor_section()
    if vs:
        out["vendors"] = vs
        with open("iowa_medicaid_data.json", "w") as f:
            json.dump(out, f, separators=(",", ":"))
    cb = county_budget_section()
    if cb:
        out["county_budget"] = cb
        with open("iowa_medicaid_data.json", "w") as f:
            json.dump(out, f, separators=(",", ":"))
        mh = [a for a in cb["counties"].get("POLK", {}) if re.search(r"mental|mh|hospital", a, re.I)]
        print("\ncounty budget: %d counties, %d service areas, FY%s..FY%s; Polk MH/hospital-ish areas: %s"
              % (len(cb["counties"]), len(cb["statewide"]), cb["fiscal_years"][0],
                 cb["fiscal_years"][-1], mh or "none flagged"))
    print("\nplace iowa_medicaid_data.json next to iowa-medicaid.html")

if __name__ == "__main__":
    main()
