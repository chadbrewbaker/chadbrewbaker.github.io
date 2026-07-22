---
layout: post
title: "Auditing Iowa Medicaid with latent-space search: $8.6B, three counties, three hospitals, and one stubborn outlier"
date: 2026-07-22
tags: [iowa, medicaid, open-data, llm, transparency]
---

Iowa Medicaid pays out about **$8.6 billion a year**. This post documents a browser suite for
that ledger — three static HTML pages and four fetch scripts, now living in
[`tools/`](https://github.com/chadbrewbaker/chadbrewbaker.github.io/tree/master/tools) — and the
open questions the data surfaced. Everything renders from committed JSON snapshots; every number
below traces to a public URI.

## Methodology: latent-space search with a frontier model

The build loop was human-executes, model-navigates. I worked with Anthropic's Claude (Fable 5),
using the model's latent knowledge of government data ecosystems as a **search heuristic over
sources that no search engine indexes well**: which agency families publish what, how state
Socrata portals migrate, what a DSH examination schedule looks like, where CMS hides its DCAT
catalog. The model proposed dataset identities and fetch code; I ran everything locally and
pasted logs back; the logs falsified or confirmed; repeat.

That loop mattered because the terrain shifted mid-project. Iowa migrated data.iowa.gov off
Socrata onto a new "Data Hub" in August 2025, breaking every legacy API ID. The model's guesses
about the new world were treated as hypotheses, not facts — several were wrong, and the fetch
scripts grew fallback chains (hub ID → CKAN discovery → legacy Socrata → manual override)
precisely because reality kept voting. The strongest example of the epistemics: an early
extraction of the state's DSH audit schedules **misassigned columns**, briefly manufacturing a
fake "UIHC DSH collapse." Uploading the full PDFs caught it; the corrected pages carry an
explicit retraction rather than a silent edit. Latent-space search finds doors fast; only
receipts open them.

Data URIs the suite runs on:

- **Iowa Data Hub** (all CC-BY, monthly): [dataset 974](https://data.iowa.gov/catalog/dataset/974)
  Medicaid payments by service category × month (2011→); [973](https://data.iowa.gov/catalog/dataset/973)
  by county × month with eligibles; [975](https://data.iowa.gov/catalog/dataset/975) by
  LTC facility × month; [939](https://data.iowa.gov/catalog/dataset/939) county budgets by
  service area (FY2005→).
- **Iowa Auditor of State DSH examinations** (SPRY 2017 & 2021):
  [legis.iowa.gov/docs/publications/ADRPT/1208822.pdf](https://www.legis.iowa.gov/docs/publications/ADRPT/1208822.pdf),
  [1518523.pdf](https://www.legis.iowa.gov/docs/publications/ADRPT/1518523.pdf).
- **CMS Hospital Provider Cost Reports** (HCRIS CMS-2552-10) via the
  [data.cms.gov](https://data.cms.gov) DCAT catalog — FY2012–2024 for our hospitals.
- **Hospital price-transparency MRFs** (45 CFR 180) discovered via each hospital's
  `/cms-hpt.txt` — including payer-specific negotiated rates for Medicaid MCO plans.
- **IRS 990s** via [ProPublica Nonprofit Explorer](https://projects.propublica.org/nonprofits/);
  **federal single audits** via the [Federal Audit Clearinghouse API](https://api.fac.gov).
- **Census** ACS/decennial for population (now API-key-gated — see gripes below).

## What the ledger shows

- **Managed care ate the ledger.** Capitation was 0% of payments through 2015; IA Health Link
  launched April 2016; the MCO line is now **94.1%** of ~$7.6B in latest-12-month payments
  ($6.93B). Statewide detail by service category is FFS residue.
- **Spending: CY2019 $5.73B → CY2025 $8.63B.** Decomposed, growth is essentially all
  per-member: Polk County runs ×1.36 since 2019 on *flat* eligibles.
- **County attribution is decaying.** The county file booked **125.9%** of the category file's
  2024 total, with a "Central Office" pseudo-county absorbing ~31% of dollars (4% in 2018).
  County-level "spending" increasingly isn't.
- **The county mental-health levy is extinct.** SF 619 (2021) took statewide county MH/DD
  budgets from ~$134M (FY2020) to **zero** (FY2026); by FY2023 the statewide line *was* Polk.
- **DSH, corrected:** UIHC's DSH received rose **$29.0M → $64.8M** between exam years;
  Broadlawns held ~$6.5–7.2M against $8.56M/yr in its audited agreements. Broadlawns' total
  hospital cost rose **+37%** (SPRY2017→2021), UIHC **+32%**.
- **Hospital Medicaid revenue** (cost reports): UIHC $139.3M (FY2015) → **$214.8M** (FY2023);
  Adair County Memorial Hospital $1.1M (FY2012) → **$4.0M** (FY2024) — ×3.6.
- **First look inside MCO pricing** (UIHC's 20,118-code Medicaid rate book): Iowa Total Care
  and Molina pay **identical** rates; Wellpoint ~2% lower — everyone pricing off the state fee
  schedule — while Medicare Advantage pays ~**7×** Medicaid for the same procedure.

## The Adair question (open)

Adair County is the statewide per-eligible outlier: **$1,577 per eligible per month** across
only ~1,558 eligibles — $29.5M/yr through a tiny base, with enrollment share (21% of
population) perfectly normal. The obvious hypothesis was facility mix: LTC beds dominating a
small denominator. Here's the fun part: **the facility-level dataset eliminated it** — Adair's
five LTC facilities show ~$27K/yr in payments, because dataset 975 records *FFS* payments and
LTC has flowed through MCO capitation since 2016. The county hospital's cost reports add only
$4.0M of Medicaid revenue. So **at least ~$25M/yr attributed to Adair is invisible in every
facility-level public dataset** — presumably MCO-paid LTSS/waiver services to Adair-coded
members, but presumably is not a finding. Also unexplained: Adair's served/eligible ratio of
1.05, the state's highest. What would settle it: county-level **MCO encounter data**
(T-MSIS-derived LTSS tables), Adair County Memorial Hospital's audited payer mix
(auditor.iowa.gov filings; FAC shows the hospital under EIN 426037639), and an
eligibility-group mix table. The tools are pointed; the answer isn't in yet.

## Questions the Legislative Services Agency should ask

1. **Why does the State Auditor's website block automated access?** auditor.iowa.gov's
   robots.txt disallows crawlers — for *public audit reports*. A citizen can click; a citizen's
   script cannot. Public accountability documents should be bulk-accessible by design.
2. **Why is county attribution collapsing into "Central Office"** — and can retroactive
   bookings be restated to counties so the public county file stays meaningful?
3. **Publish MCO encounter-based facility payments.** Dataset 975 is honest FFS accounting of a
   world that ended in 2016. The $6.9B capitation line needs a public encounter-level
   companion — at minimum vendor × county × month, the shape 975 already has. (975 also lacks
   county/city columns; names had to be matched by string.)
4. **Reconcile the public files to the CMS-64.** The 2024 county-vs-category gap (125.9%) and
   the 2026 partial-year artifacts deserve a published crosswalk.
5. **Hospital price files need enforcement follow-through.** CMS has warned 500+ hospitals
   nationally (the Register reported an unnamed Des Moines hospital among them). In our sample:
   Broadlawns publishes five MRFs but with payer labels that defeat standard Medicaid
   filtering; Adair's file hides behind a vendor's `.aspx` endpoint. Standard-format
   compliance is what makes transparency machine-usable.
6. **Small friction, big tax:** the Census API silently began requiring keys, returning HTML
   error pages to JSON clients. Every such piece of friction compounds against citizen audit.

## Mental health and hospice: surges worth a look

From the 990 series (org-wide revenue, not Medicaid-specific — leads, not verdicts):
Johnson County's crisis infrastructure grew explosively since 2019 — **CommUnity Crisis
Services ×2.96**, **Shelter House ×2.36**, **Abbe Center ×2.25** — consistent with the
CCBHC/988/ARPA era, and worth asking which funding is structural versus expiring. Hospice and
home health tell a harder story: **EveryStep (VNS of Iowa) grew ×2.81 while running a −15.2%
margin**, and **WesleyLife is at −37.7%** with expenses growing ×1.17 against revenue ×0.85 —
the post-acute cost squeeze in one line.

**Nonprofits that could use assistance** (expenses outgrowing revenue over their last three
filings, or negative margins — read the filings via the links on the
[county panel](/tools/county-panel.html)): WesleyLife, EveryStep, Link Associates (rev ×0.94
vs exp ×1.13), Lutheran Services in Iowa (×0.94 vs ×1.15), Candeo, Orchard Place, United
Action for Youth, Goodwill of the Heartland — and CommUnity, whose ×2.96 growth at breakeven
is the classic scaling-faster-than-controls pattern. Two artifacts flagged rather than
alleged: Easterseals Iowa's +97% "margin" looks like a foundation-arm filing split, and
Genesis Development's numbers are a merger wind-down.

## The tools

[`iowa-medicaid.html`](/tools/iowa-medicaid.html) — statewide explorer (baselines to 2011,
era-split charts, per-eligible/per-capita sorting). [`county-panel.html`](/tools/county-panel.html)
— Polk/Johnson/Adair: levy extinction, debt service, org 990s + single audits, registered-address
maps, the Adair story section that recomputes its own verdict as data lands.
[`hospitals.html`](/tools/hospitals.html) — Broadlawns/UIHC/Adair: corrected DSH trail, cost
trajectories, Medicaid share. Refresh scripts (`refresh_iowa_medicaid.py`,
`fetch_polk_orgs.py`, `fetch_hospital_prices.py`) rebuild every JSON from source, print their
own diagnostics, and survived one portal migration already. Licenses: Iowa Data Hub CC-BY 4.0;
federal sources public domain; page skeletons after [simonw/tools](https://github.com/simonw/tools).

*Corrections welcome — that's the point. Every figure above has a JSON snapshot and a source
URI behind it, and the one error we caught mid-build is documented on the page it touched.*
