#!/usr/bin/env python3
"""fetch_polk_orgs.py — 990 financials for Polk County HCBS / mental-health /
hospice nonprofits via the ProPublica Nonprofit Explorer API, plus a
hand-verified Broadlawns Medical Center audit seed.

Stdlib only. Run:  python3 fetch_polk_orgs.py
Writes: polk_orgs.json   (990 time series per organization)
        polk_audits/     (Broadlawns DSH examination PDFs, best effort)

MATCHING IS FUZZY AND MUST BE HAND-VERIFIED: the script searches by name and
takes the best Iowa match; review the printed table, fix any wrong EIN in the
OVERRIDE_EIN map, and re-run. 990s are org-level (not facility-level, not
payer-split); Medicaid revenue appears only where the org itemizes it.
"""
import json, re, sys, time, urllib.request, urllib.parse, os
from datetime import date

API = "https://projects.propublica.org/nonprofits/api/v2"
FAC = "https://api.fac.gov"
FAC_KEY = os.environ.get("FAC_API_KEY", "")  # free instant key: https://api.data.gov/signup
# (FAC covers single audits — orgs spending $750K+ federal/yr; SEFA rows carry
#  amount expended per federal program; Medicaid = ALN 93.778)
UA = {"User-Agent": "polk-medicaid-orgs/1.0 (public 990 data snapshot)"}

# Curated roster: Polk County orgs delivering Medicaid HCBS / habilitation /
# mental health / hospice. Edit freely; (search name, kind, note).
POLK_CITIES = ("des moines","west des moines","johnston","ankeny","urbandale",
               "clive","altoona","newton","ames","grimes","waukee")
JOHNSON_CITIES = ("iowa city","coralville","north liberty","solon","tiffin",
                  "oxford","lone tree","swisher","hills")

# (primary query, [alternate queries], kind, note)
ORGS = [
    ("ChildServe", [], "hcbs", "pediatric HCBS/complex care, Johnston"),
    ("Link Associates", [], "hcbs", "ID/DD waiver services, West Des Moines"),
    ("Candeo", ["Creative Community Options", "Candeo Inc Johnston"], "hcbs", "supported community living, Johnston"),
    ("Mainstream Living", [], "hcbs", "HCBS + behavioral health, Des Moines/Ames"),
    ("Easterseals Iowa", ["Easter Seals Iowa", "Easter Seals Society of Iowa"], "hcbs", "disability services, Des Moines"),
    ("On With Life", [], "hcbs", "brain injury rehab/HCBS, Ankeny"),
    ("Community Support Advocates", ["Community Support Advocates Des Moines"], "hcbs_mh", "integrated health home, Des Moines"),
    ("Lutheran Services in Iowa", [], "hcbs_mh", "BHIS/HCBS statewide, Des Moines HQ"),
    ("Progress Industries", [], "hcbs", "ID/DD services, Newton/Polk metro"),
    ("Genesis Development", [], "hcbs", "ID/DD services, central Iowa"),
    ("Eyerly Ball Community Mental Health", [], "mh", "CMHC/CCBHC, Des Moines (EIN 420942273)"),
    ("Orchard Place", [], "mh", "children's mental health, Des Moines"),
    ("Children and Families of Iowa", [], "mh", "behavioral health, Des Moines"),
    ("Youth Emergency Services and Shelter", ["Youth Emergency Services Shelter of Iowa", "YESS Des Moines"], "mh", "YESS, Des Moines"),
    ("EveryStep", ["EveryStep Care and Support Services", "Visiting Nurse Services of Iowa"], "hospice_hcbs", "hospice + home care (fka VNS of Iowa), Des Moines"),
    ("WesleyLife", [], "hospice_hcbs", "senior services + hospice, Johnston"),
]
ORGS_JOHNSON = [
    ("Systems Unlimited", ["Systems Unlimited Inc Iowa City"], "hcbs",
     "large ID/DD HCBS provider, Iowa City"),
    ("Successful Living", ["Successful Living Iowa City"], "hcbs_mh",
     "supported community living, Iowa City"),
    ("Reach For Your Potential", [], "hcbs", "ID/DD services, Iowa City"),
    ("Mayors Youth Empowerment Program", ["Mayor's Youth Empowerment Program"], "hcbs",
     "youth/DD services (MYEP), Iowa City"),
    ("CommUnity Crisis Services", ["Johnson County Crisis Center", "Crisis Center of Johnson County"],
     "mh", "crisis services + food bank, Iowa City"),
    ("Shelter House Community Shelter", ["Shelter House Iowa City"], "mh",
     "housing + behavioral health services, Iowa City"),
    ("Prelude Behavioral Services", ["MECCA Services"], "mh",
     "substance use / behavioral health (fka MECCA), Iowa City"),
    ("Iowa City Hospice", [], "hospice_hcbs", "nonprofit community hospice"),
    ("United Action for Youth", [], "mh", "youth counseling/MH, Iowa City"),
    ("Arc of Southeast Iowa", ["The Arc of Southeast Iowa"], "hcbs", "DD services, Iowa City"),
    ("Goodwill of the Heartland", [], "hcbs", "employment/day services incl. waiver, Iowa City area"),
    ("Abbe Center for Community Mental Health", ["Abbe Community Mental Health"], "mh",
     "CMHC; Linn-based but operates GuideLink Center in Johnson — flag geography"),
]
ADAIR_CITIES = ("greenfield", "fontanelle", "adair", "orient", "bridgewater", "casey")
ORGS_ADAIR = [
    ("Adair County Health System", ["Adair County Memorial Hospital"], "hospital",
     "county-owned hospital + LTC — likely governmental (no 990); checking anyway"),
    ("Adair County Health System Foundation", [], "foundation",
     "fundraising arm, if it exists as a separate 501c3"),
]
COUNTIES = {
    "polk":    {"cities": POLK_CITIES,    "orgs": ORGS},
    "johnson": {"cities": JOHNSON_CITIES, "orgs": ORGS_JOHNSON},
    "adair":   {"cities": ADAIR_CITIES,   "orgs": ORGS_ADAIR},
}

UIHC_SEED = {
    "org": "University of Iowa Hospitals & Clinics (state-owned, Board of Regents)",
    "no_990_reason": "governmental (state) — audited by Iowa Auditor of State; financials via Regents",
    "dsh_examinations_note": ("Extracted rows live in polk_data.json under dsh_schedules_all_hospitals "
        "as hospital 'Clinics' (name truncation of 'University of Iowa Hospitals and Clinics'). "
        "SPRY2017: limit $61,974,783, DSH $33,292,610, FFS $142,214,078, MCO $26,410,487, "
        "total $201,917,175. SPRY2021: limit $69,655,495, DSH $1,459,805, FFS $255,041,066, "
        "MCO $67,650,572, total $344,151,443. The large DSH swing between exam years reflects "
        "program restructuring — verify against UIHC financial statements before narrating."),
    "more": ["Iowa Auditor of State annual UIHC audit reports (legis.iowa.gov ADRPT)",
             "Board of Regents financial reports; HCRIS hospital cost report (Medicaid days/charges)",
             "State checkbook / Regents vendor expenditure dataset on the Iowa Data Hub"],
}
OVERRIDE_EIN = {
    # verified: Candeo (Johnston, fka Creative Community Options) — name search
    # otherwise lands on the unrelated Candeo Counseling Center
    "Candeo": "421388521",
}

# Hand-verified Broadlawns figures (governmental: no 990; audits instead).
BROADLAWNS_SEED = {
    "org": "Broadlawns Medical Center (Polk County public hospital)",
    "no_990_reason": "governmental unit; disclosure via audited financial statements and county budget",
    "hand_verified": [
        {"item": "DSH agreement FY2019", "period": "2018-07..2019-06",
         "dsh_payment": 10282070,
         "source": "BMC FY2020 audited financial statements (broadlawns.org)"},
        {"item": "DSH agreement FY2020-FY2022", "period": "2019-07..2022-06",
         "dsh_payment_per_year": 8560647, "igt_paid_per_year": 3239510,
         "note": "county tax funds provide the nonfederal share",
         "source": "BMC FY2020 audited financial statements (broadlawns.org)"},
        {"item": "payer mix FY2021", "medicaid_share": 0.62,
         "source": "Broadlawns Community Benefit Report, Jan 2021"},
    ],
    "audit_pdfs": [
        # Iowa DSH examinations (Auditor of State, published via legislature)
        "https://www.legis.iowa.gov/docs/publications/ADRPT/1518523.pdf",   # SFY2021 DSH exam
        "https://www.legis.iowa.gov/docs/publications/ADRPT/1208822.pdf",   # earlier DSH exam
    ],
    "more": ["https://www.broadlawns.org (Financial Statements page)",
             "checkbook.iowa.gov vendor search: BROADLAWNS"],
}

def get_json(url, extra_headers=None):
    h = dict(UA)
    if extra_headers:
        h.update(extra_headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def fac_get(path, params):
    if not FAC_KEY:
        raise RuntimeError("no FAC_API_KEY set")
    url = FAC + path + "?" + urllib.parse.urlencode(params)
    return get_json(url, {"X-Api-Key": FAC_KEY})

def fac_awards_for_ein(ein, since_year=2016):
    """SEFA summary per audit year: total federal expended + Medicaid (93.778)."""
    gen = fac_get("/general", {"auditee_ein": "eq." + str(ein).zfill(9),
                               "audit_year": "gte.%d" % since_year,
                               "limit": "40"})
    out = []
    for g in gen:
        rid = g.get("report_id")
        if not rid:
            continue
        time.sleep(0.6)
        rows = fac_get("/federal_awards", {"report_id": "eq." + str(rid), "limit": "500"})
        total = medicaid = 0.0
        progs = {}
        for a in rows:
            amt = float(a.get("amount_expended") or 0)
            pref = str(a.get("federal_agency_prefix") or a.get("aln", "")[:2] or "")
            ext = str(a.get("federal_award_extension") or a.get("aln", "")[3:] or "")
            name = a.get("federal_program_name") or ""
            total += amt
            key = (pref + "." + ext).strip(".")
            progs[key] = progs.get(key, 0) + amt
            if pref == "93" and ext.startswith("778"):
                medicaid += amt
        top = sorted(progs.items(), key=lambda kv: -kv[1])[:5]
        out.append({"audit_year": g.get("audit_year"),
                    "auditee_name": g.get("auditee_name"),
                    "total_federal_expended": round(total, 2),
                    "medicaid_93_778": round(medicaid, 2),
                    "top_programs": [{"aln": k, "expended": round(v, 2)} for k, v in top]})
    return sorted(out, key=lambda x: x.get("audit_year") or 0)

def norm(s):
    return re.sub(r"[^a-z0-9 ]", "", s.lower())

def score(query, cand_name, cand_state, cand_city, cities=()):
    q, c = norm(query), norm(cand_name or "")
    s = 0.0
    qw = set(q.split())
    cw = set(c.split())
    s += 2.0 * len(qw & cw) / max(1, len(qw))
    if c.startswith(q[:12]): s += 1.0
    if (cand_state or "") == "IA": s += 1.5
    if norm(cand_city or "") in cities: s += 0.5
    return s

BLACKLIST = re.compile(r"\b(church|ministr|parish|pta|booster|auxiliary)\b", re.I)
MIN_SCORE = 2.6            # word overlap + Iowa; below this = no confident match

def candidates(queries, cities=()):
    seen, out = set(), []
    for q in queries:
        for params in ({"q": q, "state[id]": "IA"}, {"q": q}):
            try:
                res = get_json(API + "/search.json?" + urllib.parse.urlencode(params))
            except Exception:
                continue
            for o in (res.get("organizations") or res.get("orgs") or []):
                ein = str(o.get("ein"))
                if ein in seen:
                    continue
                seen.add(ein)
                if BLACKLIST.search(o.get("name") or "") and not BLACKLIST.search(q):
                    continue
                o["_score"] = max(score(q2, o.get("name"), o.get("state"), o.get("city"), cities) for q2 in queries)
                out.append(o)
            if out:
                break                      # state-filtered search worked for this query
        time.sleep(0.6)
    return sorted(out, key=lambda o: -o["_score"])

def filings_of(ein):
    ein = str(ein).zfill(9)              # API 404s on unpadded EINs with leading zeros
    d = get_json(API + "/organizations/%s.json" % ein)
    org = d.get("organization", {})
    global _SCHEMA_SHOWN
    if not globals().get("_SCHEMA_SHOWN"):
        _SCHEMA_SHOWN = True
        print("    [debug] org object keys:", sorted(k for k in org.keys())[:25])
    out = []
    for f in (d.get("filings_with_data") or []):
        out.append({"year": f.get("tax_prd_yr"),
                    "revenue": f.get("totrevenue"),
                    "expenses": f.get("totfuncexpns"),
                    "assets": f.get("totassetsend"),
                    "liabilities": f.get("totliabend"),
                    "pdf": f.get("pdf_url")})
    for f in (d.get("filings_without_data") or []):
        out.append({"year": f.get("tax_prd_yr"), "revenue": None,
                    "expenses": None, "pdf": f.get("pdf_url"),
                    "note": "document only; no extracted financials"})
    out.sort(key=lambda f: (f.get("year") or 0))
    return org, out

def main():
    result = {"generated": date.today().isoformat(),
              "source": "ProPublica Nonprofit Explorer API (IRS Form 990 data)",
              "hand_verify": "MATCHES ARE FUZZY — review names/EINs below, use OVERRIDE_EIN to correct",
              "broadlawns": BROADLAWNS_SEED,
              "orgs": []}
    result["uihc"] = UIHC_SEED
    result["counties"] = {}
    for county, cfg in COUNTIES.items():
        print("\n===== %s county roster =====" % county.upper())
        print("%-42s %-11s %-26s %s" % ("query", "EIN", "matched name", "filings"))
        county_orgs = []
        result["counties"][county] = {"orgs": county_orgs}
        for query, alts, kind, note in cfg["orgs"]:
            time.sleep(1.1)                       # politeness
            try:
                if query in OVERRIDE_EIN:
                    cands = [{"ein": OVERRIDE_EIN[query], "name": "(override)",
                              "city": "", "ntee_code": "", "_score": 99}]
                else:
                    cands = candidates([query] + alts, cfg["cities"])
                chosen = None
                for m in cands[:4]:            # walk down until real filings appear
                    if m["_score"] < MIN_SCORE:
                        break
                    try:
                        time.sleep(1.1)
                        org, filings = filings_of(m.get("ein"))
                    except Exception:
                        continue
                    if any(f.get("revenue") is not None for f in filings):
                        chosen = (m, org, filings)
                        break
                    if chosen is None:
                        chosen = (m, org, filings)     # keep best doc-only as fallback
                if not chosen:
                    print("%-42s NO CONFIDENT MATCH (top: %s)" %
                          (query, cands[0]["name"][:30] + " s=%.1f" % cands[0]["_score"] if cands else "none"))
                    county_orgs.append({"query": query, "kind": kind, "note": note,
                                        "matched": None,
                                        "top_rejected": cands[0]["name"] if cands else None})
                    continue
                m, org, filings = chosen
                ein = str(m.get("ein")).zfill(9)
                years = [f["year"] for f in filings if f.get("revenue") is not None]
                print("%-42s %-11s %-26s %d filings (%s..%s)" %
                      (query, ein, (org.get("name") or m.get("name", ""))[:26],
                       len(filings), min(years) if years else "?", max(years) if years else "?"))
                entry = {
                    "query": query, "kind": kind, "note": note,
                    "matched": {"ein": ein, "name": org.get("name") or m.get("name"),
                                "city": org.get("city") or m.get("city"),
                                "ntee": org.get("ntee_code") or m.get("ntee_code"),
                                "match_score": m["_score"]},
                    "filings": filings}
                if FAC_KEY:
                    try:
                        time.sleep(0.6)
                        fac = fac_awards_for_ein(ein)
                        if fac:
                            entry["single_audits"] = fac
                            my = fac[-1]
                            print(" " * 12 + "FAC: %d audits; latest %s fed $%s (Medicaid $%s)" %
                                  (len(fac), my["audit_year"],
                                   "{:,.0f}".format(my["total_federal_expended"]),
                                   "{:,.0f}".format(my["medicaid_93_778"])))
                    except Exception as e:
                        entry["single_audits_error"] = str(e)
                county_orgs.append(entry)
            except Exception as e:
                print("%-42s ERROR %s" % (query, e))
                county_orgs.append({"query": query, "kind": kind, "note": note,
                                    "error": str(e)})
    # Geocode registered addresses (Census geocoder, free/keyless) for the map.
    # Registered address = HQ as filed with the IRS, NOT service-delivery sites.
    GEOCODE = ("https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
               "?benchmark=Public_AR_Current&format=json&address=")
    print("\ngeocoding registered addresses (Census geocoder)...")
    for county in result["counties"].values():
        for o in county["orgs"]:
            m = o.get("matched")
            if not m or not m.get("address"):
                continue
            oneline = "%s, %s, %s %s" % (m["address"], m.get("city", ""),
                                          m.get("state", "IA"), m.get("zipcode", ""))
            try:
                time.sleep(0.7)
                g = get_json(GEOCODE + urllib.parse.quote(oneline))
                matches = g.get("result", {}).get("addressMatches", [])
                if matches:
                    c = matches[0]["coordinates"]
                    m["lat"], m["lon"] = round(c["y"], 5), round(c["x"], 5)
                    m["geocoded_address"] = matches[0].get("matchedAddress", oneline)
                else:
                    m["geocode_note"] = "no match for: " + oneline
            except Exception as e:
                m["geocode_note"] = "geocoder error: %s" % e
    ok = sum(1 for cc in result["counties"].values() for o in cc["orgs"]
             if o.get("matched", {}) and o.get("matched").get("lat"))
    print("  geocoded %d org addresses" % ok)

    # Governments & state institutions (IGT / MHDS / ARPA / university money): find by name
    GOV_LOOKUPS = [
        ("polk_county_government", "*POLK COUNTY*", r"^\s*POLK COUNTY(\s|$|,)"),
        ("johnson_county_government", "*JOHNSON COUNTY*", r"^\s*JOHNSON COUNTY(\s|$|,)"),
        ("university_of_iowa", "*UNIVERSITY OF IOWA*", r"^\s*(THE\s+)?UNIVERSITY OF IOWA(\s|$|,)"),
        ("adair_county_government", "*ADAIR COUNTY*", r"^\s*ADAIR COUNTY(\s|$|,)"),
        # county hospitals hit the $750K single-audit threshold via HHS Provider
        # Relief in 2020-22, so the hospital itself likely has FAC entries:
        ("adair_county_health_system", "*ADAIR COUNTY HEALTH*", r"^\s*ADAIR COUNTY (HEALTH|MEMORIAL)"),
    ]
    if FAC_KEY:
        for key, pattern, must in GOV_LOOKUPS:
            try:
                time.sleep(0.6)
                gen = fac_get("/general", {"auditee_name": "ilike." + pattern,
                                           "auditee_state": "eq.IA",
                                           "audit_year": "gte.2016", "limit": "60"})
                eins = {}
                for g in gen:
                    eins.setdefault(g.get("auditee_ein"), g.get("auditee_name"))
                print("\n%s FAC candidates (review):" % key)
                for e2, nm in eins.items():
                    print("   EIN %s  %s" % (e2, nm))
                good = [e2 for e2, nm in eins.items()
                        if nm and re.match(must, nm.upper())
                        and not re.search(r"HEALTH SERV|CONSERV|SCHOOL|FOUNDATION|COMMUNITY|EXTENSION", nm.upper())]
                if good:
                    result[key] = {"ein": good[0], "single_audits": fac_awards_for_ein(good[0])}
            except Exception as e:
                print("FAC lookup failed for %s: %s" % (key, e))
    else:
        print("\n(no FAC_API_KEY set — skipping single-audit SEFA data; free key at https://api.data.gov/signup,")
        print(" then:  FAC_API_KEY=yourkey python3 fetch_polk_orgs.py )")

    # ---- Hospital cost reports (Broadlawns + UIHC) via data.cms.gov ----
    try:
        print("\ndiscovering Hospital Provider Cost Report (data.json is big; ~30s)...")
        cat = get_json("https://data.cms.gov/data.json")
        hosp_rows = []
        for ds in cat.get("dataset", []):
            if "hospital provider cost report" not in (ds.get("title") or "").lower():
                continue
            for dist in ds.get("distribution", []):
                au = dist.get("accessURL") or ""
                if "data-api" not in au or not au.endswith("/data"): continue
                try:
                    time.sleep(0.6)
                    for row in get_json(au + "?" + urllib.parse.urlencode({"filter[State Code]": "IA", "size": "500"})):
                        nm = str(row.get("Hospital Name") or "").upper()
                        if "BROADLAWNS" in nm or "UNIVERSITY OF IOWA" in nm or ("ADAIR" in nm and ("MEMORIAL" in nm or "HEALTH" in nm or "COUNTY" in nm)):
                            row["_dist"] = dist.get("title") or au
                            hosp_rows.append(row)
                except Exception as e:
                    print("   distribution failed:", e)
        if hosp_rows:
            with open("hospitals_data.json", "w") as f:
                json.dump({"generated": date.today().isoformat(),
                    "source": "data.cms.gov Hospital Provider Cost Report (HCRIS 2552-10)",
                    "note": ("Rows verbatim as served; fiscal years as filed, not settled. "
                             "Medicaid columns vary by release - detected by name at render."),
                    "rows": hosp_rows}, f, indent=1)
            print("wrote hospitals_data.json: %d rows" % len(hosp_rows))
        else:
            print("no Broadlawns/UIHC rows found - check data.cms.gov manually")
    except Exception as e:
        print("hospital cost report pull failed:", e)

    with open("county_orgs.json", "w") as f:
        json.dump(result, f, indent=1)
    compat = dict(result)
    compat["orgs"] = result["counties"]["polk"]["orgs"]
    with open("polk_orgs.json", "w") as f:
        json.dump(compat, f, indent=1)
    print("\nwrote county_orgs.json (all counties) + polk_orgs.json (back-compat)")
    print("review the match tables above before trusting them")

    os.makedirs("polk_audits", exist_ok=True)
    for url in BROADLAWNS_SEED["audit_pdfs"]:
        name = os.path.join("polk_audits", url.rsplit("/", 1)[-1])
        if os.path.exists(name):
            continue
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r, open(name, "wb") as f:
                f.write(r.read())
            print("downloaded", name)
        except Exception as e:
            print("could not download %s: %s (grab it manually)" % (url, e))

if __name__ == "__main__":
    main()
