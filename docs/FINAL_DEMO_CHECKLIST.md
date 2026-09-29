# SIH26108 - Final Demo Checklist & Runbook

**Project**: AI-Powered Recommendation Engine for Identifying Applicable Indian Standards for Procurement Specifications  
**Environment**: Production Stable Freeze (`EMBEDDING_PROVIDER=fallback`, `retrieval_mode=IN_MEMORY`)  
**Verified Source of Truth**: `data/real/standards_catalogue.json` (21 Standards) & `data/real/qco_registry.json` (5 QCO Mandates)

---

## 1. System Startup Commands

### Backend Server (FastAPI on Port 8000)
```powershell
cd "E:\project 1"
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Server (React + Vite on Port 5173)
```powershell
cd "E:\project 1\frontend"
npm run dev
```

---

## 2. Health & Status Verification

### Health API Endpoint
```powershell
curl http://127.0.0.1:8000/api/health
```
**Expected Response**:
```json
{
  "status": "healthy",
  "project": "SIH26108 - Indian Standards Recommendation Engine",
  "version": "1.0.0",
  "database_connected": true,
  "qdrant_connected": false,
  "neo4j_connected": false,
  "retrieval_mode": "IN_MEMORY",
  "embedding_mode": "DEMO_FALLBACK",
  "dev_mode": true
}
```

---

## 3. Sample Demo Queries & Expected Results

| # | Procurement Query | Expected Primary Standard | Verification Notes |
|---|---|---|---|
| 1 | `Heavy duty armoured PVC electric cables up to 1100 V` | **IS 1554 (Part 1):1988** | Active, Mandatory QCO Enforced, Clause grounded evidence |
| 2 | `500 kVA outdoor oil cooled distribution transformer 11 kV/433 V` | **IS 1180 (Part 1):2014** / **IS 2026** | Verified electrical power distribution standards |
| 3 | `Structural steel high strength deformed bars for concrete reinforcement Fe 500` | **IS 1786:2008** | Steel reinforcement, QCO mandatory marking |
| 4 | `Plain and reinforced concrete construction works` | **IS 456:2000** | Code of practice for plain and reinforced concrete |

*Note: Clicking sample query chips in the UI automatically populates the search box and triggers the live search pipeline.*

---

## 4. End-to-End Workflow Verification Steps

### Step A: Search & Recommendation
1. Open the UI at `http://localhost:5173`.
2. Enter the sample query: `Heavy duty armoured PVC electric cables up to 1100 V`.
3. Click **Search Standards**.
4. Verify results display:
   - Primary standard: **IS 1554 (Part 1):1988**
   - Active Lifecycle status badge (Green)
   - Mandatory QCO Order warning badge
   - Grounded clause evidence with confidence score
   - Structured parameter breakdown (Voltage: 1100 V, Material: PVC, Type: Armoured)

### Step B: Foreign Standard Statutory Precedence Warning
1. Enter query: `ASTM A36 carbon structural steel plates for fabrication`.
2. Notice the prominent statutory conflict alert:
   > *"Procurement specifies foreign standard (ASTM A36). Under Public Procurement (Preference to Make in India) Orders, Indian Standard (IS 2062:2011) takes statutory precedence."*

### Step C: Engineer Review (Approve / Modify / Reject)
1. On the recommendation card, navigate to the **Engineer Review** action buttons:
   - **APPROVE**: Approves recommendation with optional comments. Commits the record to **Verified Knowledge Memory**.
   - **MODIFY**: Allows engineer to change the primary standard or add normative references without altering source catalogue files. Saves as `MODIFIED` in Verified Knowledge.
   - **REJECT**: Marks recommendation as `REJECTED`. Preserves audit log, but strictly excludes from future Verified Memory reuse.

### Step D: Verified Knowledge Memory Reuse
1. Approve a recommendation for query `Heavy duty armoured PVC electric cables up to 1100 V`.
2. Re-run the exact or semantically similar query in the search bar.
3. Observe the green banner:
   > *"Verified Knowledge Match Found: Pre-verified by technical engineer (Status: APPROVED). Instant grounded answer."*

### Step E: Standards Management
1. Navigate to the **Standards Management** page in the UI (`/standards` or `/manage`).
2. Verify:
   - Complete list of 21 verified Indian Standards.
   - Adding a new standard via `POST /api/standards/manage/add`.
   - Modifying standard status via `PUT /api/standards/manage/{standard_number}`.
   - Preserved version history timeline via `GET /api/standards/manage/versions`.

### Step F: Document Upload & Analysis
1. Navigate to **Upload Tender** (`/upload`).
2. Upload a procurement specification (`.pdf` or `.txt`).
3. Observe real-time states:
   - `Uploading` → `Extracting Pages` → `Analyzing Requirements` → `Searching Standards` → `Completed`.
4. Verified recommendations will be displayed directly matching the tender requirements.

### Step G: Compliance & Recommendation Audit Report
1. On the search results page or recommendation detail, click **Download Report** or **Print Report**.
2. Alternatively, invoke direct API:
   - Structured JSON: `GET http://127.0.0.1:8000/api/reports/{recommendation_id}`
   - Official Printable HTML: `GET http://127.0.0.1:8000/api/reports/{recommendation_id}?format=html`
   - Direct File Download: `GET http://127.0.0.1:8000/api/reports/{recommendation_id}/download`
3. Report contains all 15 audit sections:
   1. Procurement Requirement
   2. Extracted Technical Requirements
   3. Primary Recommended Indian Standard
   4. Related Standards
   5. Normative References
   6. Lifecycle Status
   7. Last Verified Date
   8. QCO Enforcement Status
   9. Applicable Certification Scheme
   10. Foreign Standard Conflict Warning
   11. Compliance Alerts
   12. Evidence Audit Trail
   13. Engineer Review Status
   14. Verification Information
   15. Dataset & Version Information

---

## 5. Known Resilient Fallback Behaviors

| Component | Normal Provider | Fallback Behavior |
|---|---|---|
| **LLM Query Understanding** | Google Gemini (`gemini-2.5-flash`) | Automatic fallback to local regex/keyword `RuleExtractor` on 429/503/timeout. Pipeline never crashes. |
| **Embeddings** | Real BGE-M3 (Heavy) | `DEMO_FALLBACK` (384-d normalized hashing embeddings) runs 100% locally with 0MB external RAM overhead. |
| **Vector DB** | Qdrant | In-Memory Cosine Vector Store with zero external dependencies. |
| **Knowledge Graph** | Neo4j Bolt | In-Memory Graph Index for normative and supersede relationships. |

---

## 6. Regression Testing Suite

Run all verification scripts to validate system integrity:

```powershell
python scripts/verify_phase2.py      # 45/45 Passed
python scripts/verify_phase3.py      # 16/16 Passed
python scripts/verify_phase4.py      # 30/30 Passed
python scripts/verify_phase6a.py     # 62/62 Passed
python scripts/verify_system.py      # 5/5 Passed
python scripts/verify_real_demo_tests.py # 7/7 Passed (100%)
```

### Frontend Build Check:
```powershell
cd "E:\project 1\frontend"
npm run build
```
*(Must output 0 TypeScript errors).*
