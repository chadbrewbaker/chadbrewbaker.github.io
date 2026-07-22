#!/usr/bin/env python3
"""fetch_hospital_prices.py — hospital price-transparency MRFs for the suite.

Per 45 CFR 180 every licensed hospital posts a machine-readable file (MRF) of
standard charges, including PAYER-SPECIFIC NEGOTIATED CHARGES — Medicaid MCO
plans included. Discovery is standardized: /cms-hpt.txt at the hospital's web
root lists MRF locations. Rates only, no volumes: this shows MCO price terms,
never spending totals.

Stdlib only. Run:  python3 fetch_hospital_prices.py
Writes: hospital_prices.json (payer census + Medicaid-plan rates for target codes)

MRFs can be huge (academic centers: GBs). Downloads STREAM to ./mrf_cache/
(kept for re-runs). The output is a compact summary: the complete Medicaid-MCO
rate book per hospital (every code with a Medicaid-plan negotiated rate, plus
gross charge and cash price for context) — designed so the summary alone,
not the raw MRFs, carries the analysis.
"""
import os, shutil, gzip as _gzip
import csv, io, json, re, ssl, sys, urllib.request, urllib.parse
from datetime import date

def _ssl_contexts():
    yield ssl.create_default_context()
    try:
        import certifi
        yield ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    yield ctx                       # last resort, warned below

def uopen(url, timeout):
    """urlopen with a cert-fallback ladder for macOS Pythons missing CA bundles."""
    req = urllib.request.Request(url, headers=UA)
    last = None
    for i, ctx in enumerate(_ssl_contexts()):
        try:
            r = urllib.request.urlopen(req, timeout=timeout, context=ctx)
            if i == 2:
                print("   WARNING: TLS verification DISABLED for %s — fix properly by "
                      "running 'Install Certificates.command' or pip3 install certifi" % url)
            return r
        except ssl.SSLError as e:
            last = e
        except urllib.error.URLError as e:
            if isinstance(getattr(e, "reason", None), ssl.SSLError):
                last = e
            else:
                raise
    raise last

HOSPITALS = [
    ("Broadlawns Medical Center", "https://www.broadlawns.org"),
    ("University of Iowa Hospitals & Clinics", "https://uihc.org"),
    ("Adair County Health System", "https://www.adaircountyhealthsystem.org"),
]
MEDICAID_PAYER_RX = re.compile(r"medicaid|iowa total care|molina|wellpoint|amerigroup|amerihealth|caritas|ia health link|title *(19|xix)|\bt19\b|hawki|hawk-i", re.I)
# common comparison codes: MS-DRG vaginal delivery/knee, ED visit, office visit, MRI
TARGET_CODES = {"470", "807", "99284", "99213", "73721"}
MAX_ROWS_PER_HOSPITAL = 30000   # safety valve on the Medicaid rate book
UA = {"User-Agent": "iowa-medicaid-tools/1.0 (public price transparency data)"}

def get(url):
    with uopen(url, 180) as r:
        return r.read()

def download_to_cache(url):
    os.makedirs("mrf_cache", exist_ok=True)
    name = os.path.join("mrf_cache", re.sub(r"[^A-Za-z0-9._-]", "_", url.split("/")[-1])[-120:])
    if os.path.exists(name) and os.path.getsize(name) > 0:
        print("   cached: %s (%.0f MB)" % (name, os.path.getsize(name) / 1e6))
        return name
    with uopen(url, 600) as r, open(name, "wb") as f:
        shutil.copyfileobj(r, f, length=1 << 20)
    print("   downloaded: %s (%.0f MB)" % (name, os.path.getsize(name) / 1e6))
    if name.endswith(".gz"):
        plain = name[:-3]
        with _gzip.open(name, "rb") as zi, open(plain, "wb") as zo:
            shutil.copyfileobj(zi, zo, length=1 << 20)
        name = plain
    return name

def find_mrf(domain):
    txt = get(domain.rstrip("/") + "/cms-hpt.txt").decode("utf-8", "replace")
    urls = re.findall(r"(?:location-url|mrf-url):\s*(\S+)", txt, re.I)
    if not urls:
        urls = re.findall(r"(https?://\S+\.(?:json|csv)(?:\.gz)?)", txt, re.I) or \
               re.findall(r"(https?://\S+)", txt, re.I)
    return txt, urls

def summarize_csv(path):
    """Stream the CSV; build the full Medicaid rate book without loading the file."""
    f = open(path, "r", encoding="utf-8-sig", errors="replace", newline="")
    rdr = csv.reader(f)
    hdr = None
    head = []
    for r in rdr:
        head.append(r)
        if any("description" in str(c).lower() for c in r):
            hdr = [str(c).strip() for c in r]
            break
        if len(head) > 10:
            hdr = [str(c).strip() for c in head[0]]
            f.seek(0); rdr = csv.reader(f); next(rdr)
            break
    def col(rx):
        return [i for i, c in enumerate(hdr) if re.search(rx, c, re.I)]
    payer_cols = col(r"payer_name")
    plan_cols = col(r"plan_name")
    code_cols = col(r"code\|1$|^code$|billing_code")
    desc_cols = col(r"description")
    rate_cols = col(r"negotiated_dollar|negotiated_rate|estimated_allowed|estimated_amount")
    gross_cols = col(r"gross")
    cash_cols = col(r"discounted_cash|cash")
    payers = set(); book = {}; n = 0
    def first(r, cols):
        return next((r[c] for c in cols if c < len(r) and r[c]), "")
    for r in rdr:
        n += 1
        p = first(r, payer_cols)
        if p:
            payers.add(p)
        if not (p and MEDICAID_PAYER_RX.search(p)):
            continue
        code = str(first(r, code_cols)).strip()
        if not code:
            continue
        entry = book.setdefault(code, {"description": str(first(r, desc_cols))[:90],
                                       "gross": first(r, gross_cols) or None,
                                       "cash": first(r, cash_cols) or None,
                                       "medicaid_rates": {}})
        plan = first(r, plan_cols)
        key = (p + (" | " + plan if plan else ""))[:80]
        rate = first(r, rate_cols)
        if rate and len(book) <= MAX_ROWS_PER_HOSPITAL:
            entry["medicaid_rates"][key] = rate
    f.close()
    medicaid_payers = sorted(p for p in payers if MEDICAID_PAYER_RX.search(p))
    return {"format": "csv", "rows_scanned": n, "payer_count": len(payers),
            "medicaid_payers": medicaid_payers, "_payers": payers,
            "medicaid_code_count": len(book), "medicaid_rate_book": book}

def summarize_json(path):
    """Whole-file JSON load — fine on a big-RAM machine; MemoryError is caught upstream."""
    with open(path, "rb") as f:
        d = json.load(f)
    items = d.get("standard_charge_information") or []
    payers = set(); book = {}
    for it in items:
        code = ""
        desc = str(it.get("description", ""))[:90]
        for ci in it.get("code_information", []):
            code = str(ci.get("code", "")).strip() or code
        for sc in it.get("standard_charges", []):
            gross = sc.get("gross_charge"); cash = sc.get("discounted_cash")
            for pi in sc.get("payers_information", []):
                p = "%s | %s" % (pi.get("payer_name", ""), pi.get("plan_name", ""))
                payers.add(p)
                if code and MEDICAID_PAYER_RX.search(p) and len(book) <= MAX_ROWS_PER_HOSPITAL:
                    e = book.setdefault(code, {"description": desc, "gross": gross,
                                               "cash": cash, "medicaid_rates": {}})
                    r = pi.get("standard_charge_dollar") or pi.get("estimated_amount")
                    if r is not None:
                        e["medicaid_rates"][p[:80]] = r
    return {"format": "json", "items": len(items), "payer_count": len(payers),
            "medicaid_payers": sorted({p.split(" | ")[0] for p in payers if MEDICAID_PAYER_RX.search(p)}),
            "_payers": {p.split(" | ")[0] for p in payers},
            "medicaid_code_count": len(book), "medicaid_rate_book": book}

def main():
    out = {"generated": date.today().isoformat(),
           "note": ("Complete Medicaid-MCO rate books: every code with a Medicaid-plan "
                    "negotiated rate, plus gross charge and cash price. RATES, not "
                    "volumes; cannot be summed into spending."),
           "hospitals": []}
    for name, domain in HOSPITALS:
        entry = {"hospital": name, "domain": domain}
        try:
            txt, urls = find_mrf(domain)
            entry["cms_hpt_txt"] = txt[:500]
            entry["mrf_urls"] = urls
            if not urls:
                entry["error"] = "cms-hpt.txt found but no MRF URL parsed — inspect cms_hpt_txt"
            else:
                merged = None
                for u in urls:
                    path = download_to_cache(u)
                    with open(path, "rb") as fh:
                        is_json = fh.read(64).lstrip()[:1] == b"{"
                    try:
                        part = summarize_json(path) if is_json else summarize_csv(path)
                    except MemoryError:
                        entry.setdefault("errors", []).append("too large for memory: " + path)
                        continue
                    if merged is None:
                        merged = part
                        merged["payers_sample"] = sorted(part.pop("_payers", set()))[:40] if "_payers" in part else []
                    else:
                        merged["medicaid_rate_book"].update(part["medicaid_rate_book"])
                        merged["medicaid_code_count"] = len(merged["medicaid_rate_book"])
                        merged["medicaid_payers"] = sorted(set(merged["medicaid_payers"]) | set(part["medicaid_payers"]))
                        merged["payer_count"] = max(merged["payer_count"], part["payer_count"])
                        if "_payers" in part:
                            merged["payers_sample"] = sorted(set(merged.get("payers_sample", [])) | part["_payers"])[:40]
                if merged is None:
                    continue
                entry["summary"] = merged
                s = entry["summary"]
                print("%-42s %s scanned=%s payers=%d medicaid-plans=%d medicaid-codes=%d"
                      % (name[:42], s["format"], s.get("rows_scanned", s.get("items")),
                         s["payer_count"], len(s["medicaid_payers"]),
                         s["medicaid_code_count"]))
        except Exception as e:
            entry["error"] = str(e)
            print("%-42s ERROR: %s" % (name[:42], e))
        out["hospitals"].append(entry)
    for h in out["hospitals"]:
        if "summary" in h:
            h["summary"].pop("_payers", None)
    with open("hospital_prices.json", "w") as f:
        json.dump(out, f, separators=(",", ":"))
    sz = os.path.getsize("hospital_prices.json") / 1e6
    print("\nwrote hospital_prices.json (%.1f MB) — the summary IS the deliverable; "
          "upload this, not the mrf_cache/ files" % sz)
    if sz > 40:
        with open("hospital_prices.json", "rb") as fi, _gzip.open("hospital_prices.json.gz", "wb") as fo:
            shutil.copyfileobj(fi, fo)
        print("also wrote hospital_prices.json.gz for easier upload")

if __name__ == "__main__":
    main()
