# ThreatVision — Design Specification

**Version:** 1.1  
**Date:** 2026-03-29  
**Author:** Saichandram Sadhu  
**Status:** Approved baseline + amendments recorded

---

## 1. Purpose

ThreatVision is a full-stack **IOC analysis and threat intelligence** web platform: VirusTotal-style **per-vendor transparency**, with the **primary** intelligence source being the user’s **MISP** instance (Docker/self-hosted), plus **optional** external enrichers. Users analyze single or bulk IOCs, export **PDF/CSV/JSON**, and integrate **SIEM** tools (Wazuh + generic webhook).

**Core product value:** A **vendor-by-vendor breakdown** (who said what, with evidence) is **non-negotiable** and must be the **centerpiece** of the UI, exports, and API—not an afterthought to a single “black box” score.

---

## 2. Confirmed decisions (from discovery)

| Topic | Choice |
|--------|--------|
| Delivery scope | **B — Full stack v1** (full vision in product definition; implementation may still sequence milestones in-repo). |
| MISP tenancy | **C — Hybrid:** Per-user MISP in settings; **ADMIN**-configured **platform fallback** when user MISP unset. Order: user → fallback → MISP source marked unavailable for that run. |
| Browser ↔ API auth | **A — BFF:** Next.js server calls FastAPI with **short-lived internal JWT** (or equivalent). User **UUID API key** = **programmatic clients only** (not primary dashboard auth). |
| Rate limiting | **A — PostgreSQL only** for counters/windows (no Redis v1). |
| SIEM webhooks | **C — Both:** Per-user **secret** (header or path) **+** optional **HMAC + timestamp** where supported. |
| Secret encryption | **A — Single `ENCRYPTION_KEY`**; unique IV/nonce per ciphertext; rotation = operational re-encrypt. |
| Reports on AI/PDF failure | **A — Degraded:** Gemini failure → placeholder executive summary; rest of report intact. Total PDF engine failure → clear user error + retry (no silent empty file). |
| Superadmin | **B — Env + DB:** `SUPERADMIN_EMAIL` defines who **may** be superadmin; **DB role** is runtime truth; promotion only for matching email; exactly one superadmin policy enforced in application rules. |
| Architecture | **Next BFF + FastAPI** on Railway; frontend on Vercel; Postgres on Railway. |

---

## 3. System architecture (summary)

- **`threatvision/frontend`** — Next.js 14 App Router, TypeScript, Tailwind, Framer Motion, React Three Fiber / Three.js, GSAP (ScrollTrigger, counters). NextAuth (email/password, Google, GitHub).
- **`threatvision/backend`** — FastAPI, asyncpg, encryption at rest for integration secrets, IOC pipeline, PDF generation, webhooks, rate limits.
- **`threatvision/docs`** — API reference, SIEM integration guides, webhook schemas.

**Traffic:** Browser → **Next** (session cookies). Next server → **FastAPI** (internal JWT). **SSE** for bulk progress: prefer **Next proxy** of FastAPI stream to avoid cross-origin cookie complexity.

---

## 4. Vendor-by-vendor IOC breakdown (CENTERPIECE)

### 4.1 Product principle

Every analysis result MUST expose a **fixed catalog of sources** (see §4.4). For each source, the UI shows **one row** (or card column) with:

- **Source display name** (e.g. `MISP`, `AbuseIPDB`, `VirusTotal`).
- **Status:**
  - **Result:** verdict + key metadata when the call **succeeded** and source is **enabled + configured**.
  - **Not configured** — user has not supplied credentials / URL where required, or source is disabled in settings. **Greyed** treatment.
  - **Unavailable** — timeout, transport error, HTTP non-success, or parser failure. **Yellow/warning** treatment; include short reason code for support (e.g. `timeout`, `http_429`, `parse_error`).

**Configured** means: for key-based APIs, ciphertext present in DB; for keyless APIs (e.g. MalwareBazaar, ThreatFox), “configured” = **enabled** in user toggles. MISP “configured” = resolved client exists (user or fallback URL + key).

### 4.2 Canonical API shape (logical)

Each analysis returns:

- **`ioc`:** raw value, normalized value, detected `type` (`ip` \| `hash` \| `domain` \| `url` \| `email_header`).
- **`aggregate`:** `verdict` (`CLEAN` \| `SUSPICIOUS` \| `MALICIOUS`), `confidence` 0–100, optional `rationale` string for tooltips.
- **`sources[]`:** ordered array aligned to the **platform source catalog** (same order in UI, PDF, and bulk):

```json
{
  "id": "misp",
  "displayName": "MISP",
  "status": "ok | not_configured | unavailable",
  "verdict": "clean | suspicious | malicious | unknown | null",
  "detailLines": ["Event: APT28 Campaign", "Tags: botnet, tor-exit"],
  "metadata": {},
  "errorCode": null
}
```

- **`verdict`** may be `null` when `status !== ok`.
- **`detailLines`** are short, human-readable bullets (3–6 max in table; full detail in expandable panel / JSON).

### 4.3 MISP-specific richness (when `status === ok`)

`metadata` (and/or typed sub-object) MUST support **multiple matches**:

- **`events[]`:** for each match:
  - `eventId`, `eventName`
  - `tags[]` (event + attribute context where available)
  - `tlp`: `WHITE` \| `GREEN` \| `AMBER` \| `RED` (or `unknown` if absent)
  - **`feedName`** when derivable from MISP (e.g. feed metadata, event source, tag patterns, or correlation to known feed objects—implementation maps whatever MISP exposes; if only `Orgc`/`source` exists, show that as fallback label)
- If **multiple events** match, the **row** summarizes count; **expand** lists all events with IDs, names, TLP, tags, and feed/source label per event.

### 4.4 Platform source catalog (v1)

All of these appear in **every** single-IOC view, bulk dot row, and PDF table (same column order):

| `id` | Display name | Config | Notes |
|------|----------------|--------|--------|
| `misp` | MISP | URL + key (user or fallback) | Primary |
| `virustotal` | VirusTotal | API key | Rate limits |
| `abuseipdb` | AbuseIPDB | API key | IP-oriented |
| `otx` | AlienVault OTX | API key | Often optional key |
| `shodan` | Shodan | API key | IP/host |
| `urlscan` | URLScan.io | API key | URL-oriented |
| `malwarebazaar` | MalwareBazaar | none | Keyless |
| `threatfox` | ThreatFox | none | Keyless |
| `safebrowsing` | Google Safe Browsing | API key | Quota |
| `greynoise` | GreyNoise Community | API key | Community tier |
| `ibm_xforce` | IBM X-Force | API key | Tier limits |

**Not applicable** sources (e.g. hash-only APIs for an IP IOC) still appear as a row with **`verdict: unknown`** and a **single detail line** `Not applicable for this IOC type` (not “Not configured”), unless the product prefers hiding N/A sources—**default: show row** for layout consistency with VirusTotal-style grids.

### 4.5 Aggregate verdict

Weighted **consensus** remains for `aggregate.verdict` and `confidence`, but the **UI must not collapse** the story: the **per-source table** is primary; aggregate is a **header summary** (e.g. “MALICIOUS (94/100)”).

### 4.6 PDF reports

For **each IOC** section:

- Repeat the **same per-vendor table** (Source | Verdict | Key metadata / detail lines).
- Include **MISP multi-event** block when applicable (event ID, name, TLP, tags, feed/source).
- Executive summary (Gemini) references **which sources agreed** (by name), without inventing vendors that did not run.

### 4.7 Dashboard — recent activity

Each activity item includes:

- IOC snippet, aggregate verdict, timestamp.
- **“Flagged by:”** chips or inline list: **only sources** that returned `malicious` or `suspicious` (and MISP event name/tag summary for MISP).

### 4.8 Bulk analysis — mini vendor grid

- Each result row includes a **horizontal dot strip** (fixed source order = catalog).
- **Dot colors:** red / yellow / green / grey (not configured) / outlined-yellow or similar (unavailable)—**specify tokens in UI kit** to match palette (`#ff2d55`, `#ff9500`, `#00ff88`, muted grey, warning amber).
- **Tooltip** on hover: `Vendor name` + line break + `Verdict` + optional one-line detail.
- Table remains sortable/filterable on aggregate verdict, type, date; optional filter “any source = malicious”.

### 4.9 Single-IOC results page layout (UX priority)

- **Above the fold:** IOC header + aggregate verdict + confidence gauge.
- **Immediately below:** **Full-width vendor breakdown** (table or bento cards)—this is the **hero** section.
- Secondary: map (IP), MISP event deep-dive, related IOCs, timeline, actions (Add to MISP, Export PDF).

### 4.10 MISP Instance Explorer (KEY DIFFERENTIATOR)

When a user connects a MISP instance, ThreatVision **discovers and surfaces** that instance’s operational picture in the UI. This is a **key differentiator**: transparency into feeds, sync partners, taxonomies, and health—not only IOC hits.

**Backend:** All data is fetched from the user’s **resolved MISP client** (user settings first, else platform fallback per §2). Normalize responses to a stable JSON schema for the frontend. Where MISP’s REST API does not expose a field exactly as named below, map the **closest available** field and document gaps in `docs/` (e.g. “cache age” may be derived from `timestamp` / job metadata or omitted with `unknown`).

#### 4.10.1 Feeds discovery

- Call MISP **`/feeds`** (or PyMISP equivalent).
- For **each feed**, display:
  - **Feed name** (e.g. “CIRCL OSINT Feed”, “Botvrij.EU”, “MalwareBazaar”).
  - **Feed URL / source** identifier.
  - **Feed type** (e.g. MISP, CSV, freetext—map from MISP’s `source_format` / API).
  - **Enabled / disabled** status.
  - **Last fetch timestamp** (from feed/job fields when present).
  - **Event count from this feed** (best-effort: attribute/event correlation when MISP exposes linkage; otherwise estimate via search/metadata—document methodology).
  - **Live sync ON/OFF** — whether MISP is configured to pull this feed (enabled + scheduling semantics as exposed by API).
  - **Cache age** — age of local cached feed data when the API provides a timestamp; else `unknown`.

#### 4.10.2 Connected servers / sync partners

- Fetch **`/servers`** (sync connections).
- Per server:
  - **Name + URL**
  - **Sync direction** (push / pull / both) from MISP fields.
  - **Last sync timestamp** and **status** (`success` | `failed` | `never` / unknown).
  - **Event count synced** when derivable; else `unknown`.

#### 4.10.3 Taxonomies & tags in use

- Fetch **enabled taxonomies** from MISP (taxonomy API).
- Display list (e.g. TLP, MISP, Admiralty, …) for user awareness.

#### 4.10.4 MISP statistics panel

Aggregate and show (from MISP `users/statistics` / `attributes/statistics` / version endpoint as available):

- Total **events**, **attributes**, **objects**
- Total feeds **configured** vs **enabled** (actively syncing)
- Total **connected servers**
- **MISP version**
- **Last event added** timestamp (instance-wide, when available)

#### 4.10.5 Live sync status indicator

- **UI:** Green pulse = syncing activity; grey = idle; red = error (derived from last feed fetch errors or instance status if exposed).
- **Refresh:** Poll backend every **30s** or **SSE** subscription from FastAPI that pushes explorer snapshots (either is acceptable; pick one in implementation for consistency with bulk SSE).

#### 4.10.6 UI placement

- **Settings → MISP:** After **Test Connection** succeeds, expand/show the **full MISP Explorer** panel below the form.
- **Main dashboard:** **MISP Health** widget:
  - Connected / Disconnected
  - “X feeds active, Y feeds disabled”
  - Last sync: relative time (e.g. “2 minutes ago”)
  - Total events (from last explorer snapshot)
  - **Click** → navigates to full explorer (**`/settings/misp`**).
- **Dedicated page:** **`/settings/misp`** — full layout (see §4.10.7).

#### 4.10.7 MISP Explorer page (`/settings/misp`)

Full-page experience including:

- **MISP connection** header: status, host, version, total events.
- **Feeds** table: name, status (ON/OFF), last fetch/sync column, counts as available.
- **Sync servers** section: partner name/URL, direction, last sync, status.
- Sections for **taxonomies**, **statistics** summary, and **live sync** indicator (same data as above, consolidated).

Wireframe reference (logical, not pixel-perfect):

```
┌─────────────────────────────────────┐
│ MISP CONNECTION                     │
│ ✅ Connected — misp.homelab.local   │
│ Version: 2.4.x  |  Events: 12,847  │
├─────────────────────────────────────┤
│ FEEDS (47 total — 23 enabled)       │
│ ┌──────────────────┬───────┬──────┐ │
│ │ Feed Name        │Status │Last  │ │
│ ├──────────────────┼───────┼──────┤ │
│ │ CIRCL OSINT      │🟢 ON  │2m ago│ │
│ │ Botvrij.EU       │🟢 ON  │5m ago│ │
│ │ MalwareBazaar    │🔴 OFF │7d ago│ │
│ │ MISP Default     │🟢 ON  │1m ago│ │
│ └──────────────────┴───────┴──────┘ │
├─────────────────────────────────────┤
│ SYNC SERVERS (2)                    │
│ partner-misp.org  ↔ Last: 1hr ago  │
└─────────────────────────────────────┘
```

#### 4.10.8 Feed name in analysis results (ties to §4.3)

When an IOC matches MISP data, detail lines MUST attribute **which feed(s)** the evidence came from:

- Prefer **exact feed name** from the **Explorer feed catalog** (match event metadata, `EventTag`, distribution, `Orgc`, `source`, feed UUID, or MISP-specific correlation rules).
- Example copy:
  - `Found in: CIRCL OSINT Feed`
  - `Found in: Botvrij.EU Domain Feed`
  - `Found in: 3 feeds + 2 manual events` (when some events lack feed mapping).

Maintain a **per-request or cached feed id → display name** map populated during MISP analysis / explorer fetch so IOC results and Explorer stay consistent.

---

## 5. Key feature modules (v1 scope reminder)

- Auth, roles (SUPERADMIN / ADMIN / USER), API keys, admin dashboard.
- Settings: MISP + optional APIs, toggles, test connection, AES-256 at rest, **MISP Instance Explorer** (§4.10) and **MISP Health** dashboard widget.
- IOC engine: classification, parallel enrichers, consensus, **structured per-source results**.
- Single IOC, bulk (≤500), SSE progress, exports PDF/CSV/JSON.
- SIEM webhooks (Wazuh + generic), integration docs page.
- About page, branding, “Developed by Saichandram Sadhu.”
- Cinematic UI: login 3D scene, dashboard globe, GSAP reveals—**without obscuring** the vendor grid (contrast, readability, reduced-motion support).

---

## 6. Security & operations (short)

- HTTPS in production; CORS restricted to production frontend origin(s).
- Input sanitization on all IOC inputs; strict timeouts per vendor call.
- Rate limits in Postgres; superadmin-adjustable per user + unlimited flag.
- Webhook: per-user secret + optional HMAC; document replay window for timestamp validation.

---

## 7. Open implementation choices (non-blocking)

- **PDF library:** WeasyPrint vs ReportLab—choose based on Railway image constraints and HTML fidelity needs.
- **MISP feed → event attribution:** Best-effort correlation (see §4.10.8); document per-MISP-version behavior when feed linkage is ambiguous.

---

## 8. Next step

Execute **`threatvision/docs/plans/2026-03-29-threatvision-implementation-plan.md`** milestone-by-milestone.

---

*End of specification.*
