# BizLens Research & Fact-Check Log

Living document of market research, competitive analysis, and pitch fact-checks for **BizLens** (cash-flow forecasting for Georgian small businesses).

- **Product:** [github.com/g10rga/bizlens](https://github.com/g10rga/bizlens) · [bizlens.g1orga.dev](https://bizlens.g1orga.dev)
- **Not to confuse with:** bizlense.ai (unrelated agentic AI product)
- **Last updated:** 2026-10-19 (open-questions research pass)

---

## Table of contents

1. [Product definition (source of truth)](#1-product-definition-source-of-truth)
2. [Georgia ERP/POS sales forecasting market](#2-georgia-erppos-sales-forecasting-market)
3. [How BizLens differs from forecast providers](#3-how-bizlens-differs-from-forecast-providers)
4. [Idea viability notes](#4-idea-viability-notes)
5. [SME software adoption rates (Georgia)](#5-sme-software-adoption-rates-georgia)
6. [Pitch fact-check (full text)](#6-pitch-fact-check-full-text)
7. [Source index](#7-source-index)
8. [Open questions / next research](#8-open-questions--next-research)
9. [Café / bakery entity counts](#9-café--bakery-entity-counts)
10. [Beachhead software mix & willingness to pay](#10-beachhead-software-mix--willingness-to-pay)
11. [Partner desk research (GTM)](#11-partner-desk-research-gtm)
12. [Does BizLens model Georgian tax due dates?](#12-does-bizlens-model-georgian-tax-due-dates)
13. [Unit economics benchmarks (pre-pilot)](#13-unit-economics-benchmarks-pre-pilot)
14. [World Bank FAT 2022 (Georgia)](#14-world-bank-fat-2022-georgia)
15. [Changelog](#15-changelog)

---

## 1. Product definition (source of truth)

From the official BizLens README (`G10rga/BizLens`):

| Aspect | Definition |
|--------|------------|
| **One-line job** | “Will I have enough cash for rent, salaries, and suppliers — and when might I run short?” |
| **Audience** | Georgian bakeries, cafés, retail shops, pharmacies, salons, similar SMEs |
| **Not** | A full ERP replacement |
| **Sales capture** | Built-in POS, Lens Mode (fiscal receipt photo + OCR), CSV/Excel upload |
| **Forecast** | 30 / 60 / 90 day sales + cash-flow (best / likely / worst) |
| **Local edge** | Georgian Intelligence Layer — Orthodox holidays, Great Lent, tourism, local events; multipliers by business type |
| **Stack** | Flask API · React (Vite) · Prophet (optional) · RapidOCR · KA/EN UI · GEL |
| **Pitch framing (founder)** | Many Georgian SMEs lack POS/software and business experience; BizLens makes forward cash visibility the *main* product — easy, affordable, flexible with other tools |

---

## 2. Georgia ERP/POS sales forecasting market

**Research date:** 2026-10-19  
**Method:** English + Georgian web search; vendor/reseller pages; research agent pass  
**Canvas:** [Georgia ERP/POS Sales Forecasting Market](https://cursor.com/canvas/store-fbf4c46e-a72b-4e4c-86e0-bdfed57da669/cb58f274-4eb7-4507-b1e2-2bfb3229180a)

### Executive summary

- **Yes**, some providers offer sales/demand forecasting in Georgia.
- It is **uncommon** in the mass-market local SME POS stack.
- Full ML forecasting clusters in **enterprise overlays** and **higher-end F&B**.
- Most local shop POS systems advertise **reports and stock control only**.

### Forecasting type legend

| Label | Meaning |
|-------|---------|
| **Yes** | Dedicated statistical/ML sales or demand forecast (native or proven addon) |
| **Partial** | Trend charts, CRM pipeline, reorder helpers, ingredient/cash hints, budgeting |
| **No** | Reports/history only on public materials |
| **Unknown** | Insufficient public evidence |

### Provider matrix

| Name | Type | In Georgia? | Sales forecasting? | Notes |
|------|------|-------------|-------------------|-------|
| **SMART Demand Forecast** | Demand planning / analytics | Yes | **Yes** | ML; McDonald’s Georgia case (~83% weekly accuracy, 4-week horizon) |
| **Prodware Demand Forecasting** | AI suite for any ERP | Yes (Tbilisi) | **Yes** | Historic sales + Power BI; Dynamics-native variants |
| **GastroDigital (Syrve)** | Restaurant POS | Yes (certified partner) | **Yes** | AI sales forecasting; history, seasonality, weather, events |
| **Poster + Postie AI** | F&B POS + addon | Yes (Arealy distributor) | **Yes** | Postie AI month-end revenue forecast |
| **iiko** | F&B POS | Regional; GE thinner | **Yes** | Native sales forecast (revenue, dishes, ingredients) |
| **Microsoft Dynamics 365** | ERP | Yes (Prodware, SMART IT, BSC) | **Yes** | Demand Forecasts; Sales & Inventory Forecast |
| **SAP Business One** | ERP | Yes (RSM, FMG Soft) | **Yes** | MRP forecasts from sales history |
| **Oracle NetSuite** | Cloud ERP | Yes (iCFO) | **Yes** | Demand Planning methods |
| **1C / 1С** | ERP / trade | Yes (franchisees) | **Yes** (platform) / **Unknown** GE uptake | 1C Forecast Sales ML cloud service exists |
| **Wox** | Restaurant POS | Yes | **Partial** | Wox Analyst: ingredient needs, cash shortages |
| **BiRetail (Bivision)** | Retail BI overlay | Yes | **Partial** | AI trends/forecasting; integrates Fina, Oris, Balance, 1C |
| **Balance (+ Echo)** | Mini ERP / POS | Yes | **Partial** | Echo chart trends (regression/MA), not SKU demand planning |
| **AURA (Odoo)** | ERP / CRM / POS | Yes | **Partial** | CRM revenue forecasting + inventory reordering |
| **Activi** | POS | Yes | **No** | Ops, stock, RS.ge, reports |
| **Termino** | Retail POS | Yes | **No** | Till, stock, fiscal |
| **GTSoft** | Shop / restaurant POS | Yes | **No** | Purchase-planning = stock alerts, not predictive demand |
| **iCash** | Cloud POS | Yes | **No** | Reports and inventory |
| **Oris Market** | ERP / retail | Yes | **No** | Budgeting / analytical views; no demand forecast module found |
| **FINA Magazia** | Retail POS | Yes | **No** / weak Partial | Standard reports |
| **r_keeper (UCS Georgia)** | F&B POS | Yes | **No** native | Third-party addons exist elsewhere |
| **ERP Compact** | ERP / POS | Yes | **No** | Warehouse, POS, RS.ge, reporting |
| **Optimo** | Store / light POS | Yes (BOG-linked) | **No** (forward cash) | Sales, inventory, stats; from ~₾40/mo |

### Competitive gap (for BizLens)

1. **Largest whitespace:** SME local POS (Activi, Termino, GTSoft, iCash, Oris Market, FINA) — forecast-light.
2. **Mid-market “almost”:** Balance Echo, GTSoft purchase planning, BiRetail — appetite for forward help, not full cash runway.
3. **F&B higher end contested:** Syrve/GastroDigital, Poster+Postie, iiko, Wox, SMART DF @ McDonald’s.
4. **Enterprise ERP path is partner-led:** SAP/Dynamics/NetSuite/1C already include forecast modules — compete as specialized overlay, not replacement.

### Confidence

| Area | Confidence |
|------|------------|
| Local SME POS lack advertised forecasting | High |
| SMART Demand Forecast real Georgia deployment | High |
| Balance Echo = chart trends, not demand planning | High |
| Poster + Postie in Georgia | Medium–High |
| iiko native forecast + Georgia installed base | Medium |
| 1C Forecast Sales routinely sold in GE | Low–Medium |

---

## 3. How BizLens differs from forecast providers

| Dimension | Typical GE forecast providers | BizLens |
|-----------|------------------------------|---------|
| **Job to be done** | What will we sell / stock / staff? | Will cash run out, and when? |
| **Output** | SKU/demand/ingredient forecasts | Day-by-day cash: best / likely / worst + alerts |
| **Local seasonality** | Generic history, weather, or none | Georgian Intelligence Layer (Orthodox holidays, fasting, tourism, events by business type) |
| **How sales enter** | Locked to their POS/ERP | Light POS **or** receipt photo **or** CSV — keep existing till |
| **Product shape** | Full POS/ERP or enterprise addon | Lightweight cash-forecast app |
| **Audience** | Chains / restaurants / Dynamics–SAP buyers | Bakeries, cafés, shops, pharmacies, salons |
| **Honesty about data** | Rarely surfaced | Incomplete Lens capture widens best/worst bands |

**Mentor-ready one-liner:**  
ERP forecast optimizes *operations*; BizLens prevents *cash surprise*. More than one ERP *can* forecast — almost none of the shops in the beachhead *use* that feature, and local POS they actually use does not answer “will I make rent?” with Georgian seasonality.

**Founder positioning (refined):**  
Cash-flow foresight as the *main* product (not a buried ERP report); easy/affordable for notebook-era or light-POS Georgian SMEs; flexible with other software.

---

## 4. Idea viability notes

**Verdict:** Real potential as a focused SME cash-visibility product for Georgia — not automatic success.

### Strengths

- Clear emotional pain: timing of rent/salaries vs cash, not “can’t sell”
- Primary vs secondary feature positioning matches market gap
- Georgian seasonality is a real local moat
- Complements (doesn’t require replacing) local POS

### Risks

1. **Cold start** — forecasts need history; new shops need an honest weak→strong path  
2. **Habit** — daily capture (photo/enter sales) is the product risk, not the algorithm  
3. **Overclaim** — “never face financial problems” is too strong; better: reduce cash surprises  
4. **Validate adoption stats** — don’t invent “70% have no POS” (see §5)  
5. **Unit economics** — micro-SME pricing needs volume / partners / freemium path  

### What would strengthen the case

- 15–20 owner interviews with willingness-to-pay (₾X/month)  
- 60-second daily workflow from handwritten totals or receipt photos  
- Clear promise: “see if rent clears in 30 days”  
- Proof one bakery avoided a shortfall using an alert  

---

## 5. SME software adoption rates (Georgia)

**Research date:** 2026-10-19  
**Question:** What % of Georgian small businesses don’t use any software (POS, ERP, etc.) to track sales/products?

### Bottom line

| Claim | Status |
|-------|--------|
| Exact % with **no** sales/inventory/POS software of any kind | **Not published** by Geostat |
| “**70%** have no POS” | **Unsupported** — do not cite |
| “**85%** lack cash-crisis forecasting tools” | **Unsupported** — do not cite |
| Best official proxy | **~92–94% of small firms do not use ERP** (only ~6–8% do), 2024 |

### Official / strong proxies

| Metric | Figure | Year | Source |
|--------|------|------|--------|
| Small firms using **ERP** | ~6–8% (ISET cites 6%; academic Geostat reprint 7.7%) | 2024 | Geostat → ISET SME Digitalization |
| Small firms **without ERP** | **~92–94%** | 2024 | Derived |
| Georgian SMEs with ERP vs EU | **7% vs 42%** | 2024 | ISET |
| Small firms using **CRM** | ~3% | 2024 | ISET ← Geostat |
| Small firms with **website** | ~12% | 2024 | ISET ← Geostat |
| Enterprises with internet | ~95% | 2024 | Geostat ICT press |
| Enterprises with website | ~13.9% | 2024 | Geostat ICT press |
| No social media (enterprises) | 70.7% | 2024 | Geostat — **not POS** |

**Caveat:** Geostat ERP = integrated resource-planning class (SAP, Oracle, Dynamics examples). Excel, light POS, or some 1C shop configs may **not** count as ERP. “No ERP” **overstates** “no software of any kind.”

### Closer to paper / no digital tracking

**NBG MSME Financial Literacy Study (2021):**

- About **half** of owners keep financial records electronically (Excel *or* dedicated software)
- **Paper only:** ~**27% Tbilisi**, ~**37% regions**
- Electronic: **60% Tbilisi** vs **41% regions**

### Bank market estimate (not Geostat)

**Bank of Georgia Optimo pitch (~2020):** of ~74k registered MSME merchants, **~80% (59k) “unorganised / non-digital.”** Directional; company estimate; method not fully public; dated.

### Critical distinction

**Card POS payment terminals ≠ sales management software.**  
NBG: ~130k POS *payment* terminals (May 2025). Many shops take cards without inventory/sales software.

### Safe phrases for pitches

- “About **93% of Georgian small enterprises do not use ERP** (Geostat/ISET, 2024).”
- “Many micro businesses still use paper or Excel; NBG found **~30–40% on paper**, especially outside Tbilisi.”
- Avoid: “70% / 85% have no POS / no cash-flow tool” without a primary source.

---

## 6. Pitch fact-check (full text)

**Research date:** 2026-10-19  
**Pitch submitted by founder for fact-check.**

### Summary verdict

Problem story and product positioning are **credible**. Several **headline numbers are wrong, unsupported, or internally inconsistent**. Fix before pitching to mentors/investors.

### Claim-by-claim table

| # | Claim in pitch | Verdict | Evidence / recommended fix |
|---|----------------|---------|----------------------------|
| 1 | “Over **10,000** small businesses in Georgia” | **Misleading / understated** | ~**242k–281k active** enterprises (Geostat). 10k is far too small for *all* small businesses. |
| 2 | “**Most** of which are cafés, bakeries, and grocery stores” | **False** as written | Largest sector is **trade** (~75k active). Accommodation + food service together ≈ **9,970–11,600 active** (includes hotels). |
| 3 | Beachhead “**4,800–10,000 cafés**” / “10,000 digitally accessible” | **Unverified** | No public café-only or “digitally accessible” Geostat split. Safe: ~10k active **accommodation & food service** entities total. |
| 4 | “**85%** lack any tool capable of identifying a cash flow crisis weeks in advance” | **Unsupported** | No official figure. Use ERP proxy (~93% of small firms without ERP) or drop exact %. |
| 5 | Lack of tools → financial problems → “**ultimately business failure**” | **Overclaimed** | Cash stress is real (NBG pandemic sample: ~half faced insufficient cash flow). Causal “no forecast tool → failure” not proven for Georgia. Soften. |
| 6 | Pricing **₾49 / ₾99 / ₾149** “much lower than professional accounting” | **Mostly fair, apples-to-oranges** | Bookkeeping often ₾150–350+/mo for simple IEs. Different job (compliance vs forecast). Say cheaper *and different*. |
| 7 | **5% SOM → ARR ₾25k–75k** | **Math / label error** | 5% of 10,000 = 500 customers → **₾25k–75k is MRR**, not ARR. **True ARR ≈ ₾300k–900k/year**. |
| 8 | Gross margin **80%**, LTV **~₾2,000**, CAC **~₾200** | **Unverified / aspirational** | Mark as assumptions. LTV:CAC 10:1 is a *target*. |
| 9 | **Optimo** tracks current sales but “fails to account for future tax obligations” | **Partly fair, weakly phrased** | Optimo = POS/inventory/sales history (~₾40+). Better: “does not project *forward cash runway*.” Don’t claim tax modeling unless BizLens does RS.ge tax dates. |
| 10 | **QuickBooks** robust but ignores Georgian seasonality / local factors | **Mostly supported** | Not localized for RS.ge / Georgian tax; seasonality claim fair for niche. |
| 11 | Competitive map (Optimo + QuickBooks only) | **Incomplete** | Also: Balance, Oris, Activi, FINA, Wox, GastroDigital/Syrve, SMART DF, BiRetail, Dynamics/SAP/1C. |
| 12 | 10 interviews; all feel cash uncertainty; **2 would pay** | **Accept as primary research** | Honest but weak (20% pay intent). Don’t imply PMF yet. |
| 13 | MVP ready (Flask, React, Prophet, RapidOCR, Georgian layer) | **Plausible** | Matches GitHub README. Soften “fully ready for real-world” unless real-receipt stress-tested. |
| 14 | Café seasonality / tourism / Easter–Christmas | **Reasonable** | Qualitative; sound for Georgian HoReCa. |
| 15 | “Owners already check balances daily — not a new habit” | **Unverified** | Plausible anecdote; don’t state as fact without survey. |

### Internal inconsistencies in the pitch

1. Market size jumps: 10k small businesses → 10k cafés/bakeries → 4.8k–10k cafés → cafés and restaurants.  
2. SOM vs ARR: understates revenue ~12× by calling MRR “ARR.”  
3. Exact % claims (85%, earlier 70%) unsupported.

### Safer rewrite snippets

**Market paragraph:**

> Georgia has roughly **240,000+ active enterprises**. Our beachhead is **small cafés and bakeries** within **accommodation & food service** (~**10,000 active entities** in that sector overall — Geostat). Official data show only about **6–8% of small firms use ERP**; most lack tools that project cash weeks ahead. In interviews with **10** owners, all described cash uncertainty; **2** said they would pay for a solution.

**Revenue paragraph:**

> At 5% of a 10,000-business SOM (**500** customers), **MRR** would be ~₾25k–75k (**ARR ~₾300k–900k**), depending on mix of ₾49–149 plans — *illustrative, not a forecast*.

### What to keep from the pitch

- Problem framing (rent / payroll / supplier shock + unknown runway)  
- Cash-flow-first (not “another ERP”)  
- Three data inputs (POS / receipt photo / CSV)  
- Georgian Intelligence Layer  
- Best / likely / worst scenarios  
- Price vs full accounting (with caveat)  
- Optimo = operational; BizLens = forward cash (rephrased)  
- Honest interview sample size  

---

## 7. Source index

### Official / institutional

| Source | URL / ID | Used for |
|--------|----------|----------|
| Geostat — ICT in enterprises 2024 | https://www.geostat.ge/media/70794/Use-of-Information-Communication-Technologies-in-Enterprises---2024.pdf | Internet, website, social media |
| Geostat — Business sector 2025 | https://www.geostat.ge/media/75353/Business-sector-in-Georgia-2025.pdf | Enterprise counts, sectors |
| Geostat — Business register / by activity | https://www.geostat.ge/en/modules/categories/64/business-register · https://www.geostat.ge/en/modules/categories/65/by-kind-of-economic-activity | Active entities by NACE |
| ISET — SME Digitalization in Georgia 2024 snapshot | https://iset-pi.ge/storage/media/other/2025-09-15/d14138b0-9234-11f0-9205-a3ee28231f11.pdf · https://iset.ge/wp-content/uploads/2026/01/2.-SME-Digitalization-in-Georgia-2024-snapshot-August-2025.pdf | ERP/CRM by firm size |
| Geostat ERP tables (via paper) | https://doi.org/10.36074/grail-of-science.02.08.2024.022 | ERP % 2021–2024 by size |
| NBG — MSME Financial Literacy Study | https://finedu.gov.ge/storage/files/doc/ACT_Analytical%20Report_NBG_MSME%20survey_04.10.21(1).pdf | Paper vs electronic records |
| Bank of Georgia — Investor Day Optimo | https://ramad.bog.ge/s3/BogGroup/2024/04/BOGG-Investor-Day-2020-Digital-Ecosystems.pdf | 80% non-digital merchants (~2020) |
| World Bank / SARAS — MSME accounting needs | https://saras.gov.ge/Content/files/WB%20Business%20Report%2026152022_FINAL%20ENG_for%20send.pdf | Accounting service usage context |
| World Bank FAT Survey Georgia 2022 | https://microdata.worldbank.org/catalog/8228 | 1800 firms ≥5 employees; microdata download still needed for POS/inventory % |
| HoReCA Expo — Georgian market | https://horecaexpogeorgia.com/en/for-exhibitors/about-the-georgian-market | Secondary cite: 9,826 registered restaurants/cafés/bars (2025) |
| Geostat active entities by activity | https://www.geostat.ge/en/modules/categories/65/by-kind-of-economic-activity | Section I active ~9,970 |
| Balance Exchange API | https://balance.ge/en/api | Partner technical readiness |
| Poster distributors (Arealy GE) | https://joinposter.com/en/distributors-and-partners | Georgia distributor contacts |
| Poster for developers | https://dev.joinposter.com/en | Marketplace + API GTM path |
| Optimo | https://optimo.ge/en · info@optimo.ge | Light POS partner candidate |
| 1Soft | https://1soft.ge/ · info@1soft.ge | 1C/ERP partner candidate |
| FMG Soft | https://fmgsoft.ge/ | Multi-ERP/POS reseller |
| Mosaic B2B SaaS Benchmarks 2023 | https://info.mosaic.tech/hubfs/Downloadables%20(eBooks%2C%20Templates%2C%20and%20Reports)/2023%20B2B%20SaaS%20Benchmarks%20Report.pdf | LTV:CAC ~3.6–4.2× population |

### Product / competitor pages (sample)

| Vendor | URL |
|--------|-----|
| SMART Demand Forecast | https://sdh.smart-it.com/ge/df/ |
| McD Georgia SMART DF case | https://sdh.smart-it.com/ge/news-post/how-the-implementation-of-smart-demand-forecast-improved-the-accuracy-of-demand-forecasting-at-mcdonalds-georgia/ |
| Prodware Demand Forecasting | https://www.prodwaregroup.com/en-ge/documentation/brochures/demand-forecasting-universal-erp/ |
| GastroDigital / Syrve | https://gastrodigital.global/en/reports-analytics/ |
| Wox | https://wox.ge/ |
| BiRetail | https://bivision.ge/saas-products/biretail/ |
| Balance | https://balance.ge/en/ |
| Activi | https://activi.ge/en |
| AURA / Odoo | https://www.erpsystems.ge/en/solutions/sales |
| Optimo | https://optimo.ge/en |
| BizLens repo | https://github.com/g10rga/bizlens |
| BizLens site | https://bizlens.g1orga.dev |

### Accounting price references (Georgia)

- https://register-company.ge/blog/accounting-cost-georgia/  
- https://ganbajeba.ge/en/outsourced-accounting/  
- https://www.bookkeeping.ge/prices  

---

## 8. Open questions / next research

Status after 2026-10-19 desk-research pass:

| Item | Status | Where |
|------|--------|-------|
| Café-only / bakery-only entity counts | **Partial** — no official café-only active count; proxies documented | [§9](#9-café--bakery-entity-counts) |
| Primary survey: software mix in beachhead | **Blocked** — needs founder fieldwork; proxies + survey script | [§10](#10-beachhead-software-mix--willingness-to-pay) |
| WTP ₾49/99/149 + daily capture willingness | **Blocked** — only 2/10 interview signal; price proxies | [§10](#10-beachhead-software-mix--willingness-to-pay) |
| Partner interviews | **Desk only** — contacts/APIs found; calls not done | [§11](#11-partner-desk-research-gtm) |
| BizLens models Georgian tax due dates? | **Answered: No** | [§12](#12-does-bizlens-model-georgian-tax-due-dates) |
| Validate GM / churn / LTV / CAC with pilots | **Benchmarks only** — no pilot data yet | [§13](#13-unit-economics-benchmarks-pre-pilot) |
| World Bank FAT 2022 microdata analysis | **Partial** — dataset located; aggregates for POS/inventory not published | [§14](#14-world-bank-fat-2022-georgia) |

### Still to do (founder / next agent pass)

- [ ] Query Geostat Business Register (`br.geostat.ge`) for NACE **56.10 / 56.30** (restaurants/cafés/bars) and **10.71** (bakery manufacture) active counts  
- [ ] Run 20–30 beachhead interviews with software-mix + WTP + daily-capture questions (script in §10)  
- [ ] Call partners in §11; log outcomes here  
- [ ] Drop or rephrase pitch “future tax obligations” vs Optimo (product does not model RS.ge taxes)  
- [ ] After 10–20 paying pilots: measure churn, CAC, gross margin; replace §13 assumptions  
- [ ] Download FAT Georgia microdata (WB Microdata Library) and tabulate sales/inventory tech vars for small firms / accommodation  

---

## 9. Café / bakery entity counts

**Research date:** 2026-10-19

### What Geostat publishes publicly

| Scope | Registered | Active | Date / note | Source |
|-------|------------|--------|-------------|--------|
| **I — Accommodation and food service** (hotels + food) | 31,222 | **9,970** | Geostat activity table (snapshot ~2026) | [Geostat by activity](https://www.geostat.ge/en/modules/categories/65/by-kind-of-economic-activity) |
| Same sector | 30,871 | **11,583** | As of 1 Apr 2026 (press summary) | [Sova / Geostat](https://sovanews.tv/en/2026/04/15/geostat-only-27-of-registered-business-entities-in-georgia-are-active/) |
| Food service **turnover / employment** (not entity count) | — | Food service employees **26,397 (2024) → 27,737 (2025)** | Geostat enterprise activities | [Activities 2025 PDF](https://www.geostat.ge/media/83054/Activities-of-Enterprises---2025.pdf) |

Geostat’s public register tables **do not break out** NACE 56 (food service) vs 55 (accommodation) for **entity counts**, nor café vs restaurant vs bar.

### Best secondary cite for restaurants / cafés / bars

| Claim | Figure | Caveat |
|-------|------|--------|
| Registered restaurants, cafés and bars (2025) | **9,826** | Cited by [HoReCA Expo Georgia](https://horecaexpogeorgia.com/en/for-exhibitors/about-the-georgian-market) as Geostat/NSSG; **not verified on a Geostat CSV download in this pass**. Includes restaurants **and** bars — not café-only. |
| New restaurants/cafés/bars opened in 2024 | **1,100** | Same secondary source |

### Bakeries — classification trap

| Type | NACE | Public entity count? |
|------|------|----------------------|
| Manufacture of bakery products (bread factory / production bakery) | **10.71** (Manufacturing) | **Not found** in public Geostat tables this pass |
| Shop that heats/sells bakery for immediate consumption | **56** (Food service) | Lumped into food service / HoReCa figures |

**Pitch implication:** “Cafés and bakeries ≈ 10,000” is a **reasonable order-of-magnitude beachhead** if you mean “food-service venues overlapping restaurants/cafés/bars (~10k registered)” — but it is **not** a Geostat café-only or bakery-only active count. Do not claim café-only = 4,800–10,000 without a register extract.

### How to get exact counts next

1. Geostat Business Register: https://br.geostat.ge/register_geo/  
2. Filter NACE Rev.2: `56.10`, `56.21`, `56.29`, `56.30`, and separately `10.71` / `10.71.1`  
3. Export active vs registered; note micro vs small size if available  

---

## 10. Beachhead software mix & willingness to pay

**Research date:** 2026-10-19

### Primary survey status

**Not run in this research pass** (requires founder fieldwork). Existing primary signal from pitch: **10** owner interviews; **2** said they would pay (~20%).

### Proxies for “software mix” (not beachhead-specific)

| Segment | Proxy finding | Source |
|---------|---------------|--------|
| Small firms, Georgia | ~**6–8%** use ERP → ~**92–94%** do not | Geostat → ISET 2024 |
| Small firms | ~**3%** use CRM | Same |
| MSMEs (national) | ~**half** electronic records (Excel **or** software); **~27–37% paper** | NBG MSME Financial Literacy 2021 |
| MSME merchants (~2020) | ~**80%** “unorganised / non-digital” (BOG Optimo sizing) | BOG Investor Day 2020 |
| Payment terminals | ~**130k** card POS terminals (May 2025) — **not** management software | NBG / press |

**There is still no published %** for beachhead cafés/bakeries splitting: none / Excel / light POS (Optimo, Activi, iCash…) / full ERP.

### Willingness to pay & daily capture

| Signal | Finding |
|--------|---------|
| Founder interviews | 2/10 would pay — **directionally positive, statistically weak** |
| Price anchors in market | Optimo store software from **~₾40**/mo; outsourced accounting often **₾150–350+**/mo for simple IEs |
| BizLens tiers | ₾49 / 99 / 149 sit **between** light POS and full accounting — plausible, **unvalidated** |
| Daily capture willingness | **No survey data** |

### Recommended 5-minute interview script (run 20–30)

1. How do you track **today’s sales**? (notebook / Excel / POS name / nothing)  
2. How do you know if you can pay **rent next month**?  
3. Would you open an app **every day** for &lt;2 minutes to log sales or photo a receipt? (yes / maybe / no)  
4. At what monthly price would this be a clear yes / clear no? (prompt ₾0 / 29 / 49 / 99 / 149 / 200+)  
5. Who else helps with money decisions? (accountant / family / bank)

Log results in a sheet and paste summary % into this section when done.

---

## 11. Partner desk research (GTM)

**Research date:** 2026-10-19  
**Note:** These are **desk findings only**. Live partner interviews are still required.

| Partner | Role | Integration / partnership signal | Contact (public) | Interview status |
|---------|------|----------------------------------|------------------|------------------|
| **Optimo** | Light POS (BOG ecosystem) | Public API exists (`public-api…optimo.ge` / Swagger referenced by integrators); WooCommerce & Storera sync products exist | info@optimo.ge · (032) 2 800 900 · [optimo.ge](https://optimo.ge/en) | **Not interviewed** |
| **Balance** | Mini ERP / accounting | Documented **Balance Exchange** REST API (sales, purchases, catalogues) | [balance.ge/en/api](https://balance.ge/en/api) | **Not interviewed** |
| **Poster / Arealy** | F&B cloud POS | Poster has full developer platform + app marketplace (30% revenue share); **Arealy** is official Georgia distributor | Arealy: anna@area.ly · +995 511 233 353 · [Poster distributors](https://joinposter.com/en/distributors-and-partners) · [dev.joinposter.com](https://dev.joinposter.com/en) | **Not interviewed** |
| **1Soft** | 1C / ERP Compact / Standard; RS.ge | ERP reseller; RS.ge integration product | info@1soft.ge · +995 322 23 83 89 · Gamrekeli 2 | **Not interviewed** |
| **FMG Soft** | SAP B1, Odoo Gold, FMG Market/Restaurant, Info Enterprise | Claims **5000+** clients; Info Enterprise lists **API** + POS modules | info@fmgsoft.ge / info@fmg.ge · 032 2 47 06 00 | **Not interviewed** |
| **UCS Georgia (r_keeper)** | F&B POS | Active GE deployments historically; no open public “BizLens partner” page found this pass | Via r_keeper / UCS channels | **Not interviewed** |

### GTM implication

- **Best technical fit for add-on distribution:** Poster (marketplace + API) and Balance/Optimo (documented exchange APIs).  
- **Best volume claim:** FMG Soft (if partnership possible without competing with their own analytics).  
- Do **not** claim partner CAC ₾200 until at least one LOI or pilot referral agreement exists.

---

## 12. Does BizLens model Georgian tax due dates?

**Research date:** 2026-10-19  
**Method:** Code review of `G10rga/BizLens` (`models.py`, `cashflow.py`, `seed.py`, `TERMS_OF_SERVICE.md`)

### Verdict: **No**

| What BizLens does | What it does **not** do |
|-------------------|-------------------------|
| User-entered **FixedExpense** with `due_day` (1–28): rent, salaries, utilities, other | Automatic **VAT / income tax / RS.ge declaration** calendar |
| Recurring **SupplierPayment** every N days | Pension / payroll tax rules |
| Cash projection = forecast income − those expenses | Tax advice (TOS explicitly disclaims financial/tax advice) |

Demo seed expenses: `rent`, `salaries`, `utilities`, `other` — not tax line items.

### Pitch consequence

**Do not claim** vs Optimo: “they fail to account for future **tax** obligations” unless/until BizLens adds Georgian tax due-date modeling (e.g. 15th monthly declarations). Safer claim: Optimo tracks **past/current sales**; BizLens projects **forward cash runway** from sales + user-scheduled outflows.

---

## 13. Unit economics benchmarks (pre-pilot)

**Research date:** 2026-10-19  
**Status:** Industry benchmarks only — **BizLens has no validated GM / churn / LTV / CAC from pilots**.

### Pitch assumptions vs benchmarks

| Metric | Pitch assumption | Benchmark / check | Verdict |
|--------|------------------|-------------------|---------|
| Gross margin | **80%** | Typical software SaaS often targets ~70–85%+ | Plausible **target**, not measured |
| LTV | **~₾2,000** | At blended ~₾99/mo × 80% margin → needs ~**25 months** lifetime; at ₾49 → ~**51 months** | Sensitive to churn; unvalidated |
| CAC | **~₾200** via partners | Healthy B2B SaaS LTV:CAC often **≥3:1**; pitch implies **10:1** | Aspirational until partner CAC proven |
| LTV:CAC | Implied **10:1** | Mosaic B2B SaaS population often ~**3.6–4.2×**; &gt;5× can mean under-investment in growth | Treat 10:1 as upside case, not base case |
| Churn | Not stated | SMB / restaurant-adjacent software often sees **high logo churn** (closures + switching); do not use consumer SaaS “5% annual” fantasy for cafés | Model **monthly** churn explicitly |

### Corrected revenue illustration (from earlier fact-check)

If SOM = 10,000 and capture = 5% → **500** customers:

| Tier mix | MRR | ARR |
|----------|-----|-----|
| All ₾49 | ₾24,500 | **₾294,000** |
| All ₾99 | ₾49,500 | **₾594,000** |
| All ₾149 | ₾74,500 | **₾894,000** |

Pitch’s “ARR ₾25k–75k” was **MRR mislabeled**.

### What “validate with early pilots” means (minimum)

After **≥10 paying** customers for **≥3 months**:

1. Gross margin = (revenue − hosting/OCR/support COGS) / revenue  
2. Logo churn = cancelled / starting customers  
3. LTV ≈ ARPU × GM% / monthly churn  
4. CAC = sales+marketing+partner commissions / new customers  
5. Replace this section’s “assumption” column with measured values  

---

## 14. World Bank FAT 2022 (Georgia)

**Research date:** 2026-10-19

### Dataset facts

| Field | Value |
|-------|-------|
| Title | Firm Adoption of Technology (FAT) Survey, 2022 — Georgia |
| Catalog | https://microdata.worldbank.org/catalog/8228 |
| Cases | **1,800** firms · **969** variables |
| Universe | Formal establishments with **≥5 employees** (micros &lt;5 **excluded**) |
| Stratification | Region (East / Tbilisi / West); size (5–19, 20–99, 100+); sectors including **accommodation (ISIC 55)**, retail/wholesale, food processing, etc. |
| Response rate | 86% |
| Public release | Edited anonymised dataset (version notes ~2026-02) |

### What we could **not** complete this pass

- No secondary publication found with Georgia-specific **% using POS / inventory / sales software** from FAT.  
- Data dictionary web UI lists the file but does not expose variable-level sales/inventory tech tables without download.  
- Sample **excludes** many BizLens targets (solo / &lt;5 employee cafés and bakeries).

### How to finish the analysis

1. Register / download `fat_georgia_disclosure` from WB Microdata Library  
2. Identify general business-function tech vars for sales, inventory, payments, accounting  
3. Tabulate by size (5–19) and sector (accommodation / retail / food processing)  
4. Paste weighted % into §5 and this section  

Until then, **prefer Geostat ERP/CRM figures** for public claims; treat FAT as a high-value follow-up for “tech intensity among formal 5+ employee firms,” not for notebook-era micros.

---

## 15. Changelog

| Date | What was added |
|------|----------------|
| 2026-10-19 | Initial log: forecasting market scan, differentiation, viability notes, SME adoption stats, full pitch fact-check, source index |
| 2026-10-19 | Open-questions pass: café/bakery count proxies (§9); software-mix/WTP blockers + interview script (§10); partner desk contacts/APIs (§11); tax modeling = No (§12); unit-economics benchmarks (§13); FAT 2022 dataset status (§14) |
