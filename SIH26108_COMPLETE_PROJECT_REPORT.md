# SIH26108 — BIS SpecEngine: Complete Technical Architecture & System Report

> **Smart India Hackathon 2026**  
> **Problem Statement SIH26108**: AI-Powered Recommendation Engine for Identifying Applicable Indian Standards for Procurement Specifications  
> **Project Name**: BIS SpecEngine  
> **Environment**: Production Stable Freeze (`EMBEDDING_PROVIDER=fallback`, `retrieval_mode=IN_MEMORY`)  
> **Authoritative Source of Truth**: Curated BIS Catalogue (`data/real/standards_catalogue.json` - 21 Standards) & QCO Registry (`data/real/qco_registry.json` - 5 Mandates)

---

## 1. Project Overview & Problem Statement

Procurement officers in government departments (CPWD, MES, NHAI, RITES) and public sector undertakings often struggle to accurately identify mandatory and applicable Indian Standards (IS) for goods, civil construction works, and electrical systems specified in tenders and RFPs.

Tenders frequently:
1. Cite obsolete or superseded Indian Standards (e.g., citing `IS 456:1978` instead of `IS 456:2000`).
2. Omit mandatory Quality Control Orders (QCOs) and statutory BIS Certification schemes (Scheme I / ISI Mark).
3. Specify foreign standards (such as `ASTM A36`, `IEC`, `DIN`, `BS`, or `EN`) without referencing the equivalent Indian Standard, violating statutory Public Procurement (Preference to Make in India) orders.
4. Suffer from ungrounded recommendations and LLM hallucinations in automated systems.

**BIS SpecEngine** provides an evidence-first, deterministic, and auditable solution by enforcing:
- Parameter extraction without LLM standard hallucination.
- Evidence-first retrieval grounded in verified Bureau of Indian Standards catalogue records.
- Exact clause and page provenance for all recommendations.
- Statutory compliance enforcement for Quality Control Orders (QCOs) and Make-in-India precedence.
- An interactive knowledge graph modeling normative dependencies and mandatory testing methods (`IS 10810`, `IS 516`, `IS 2386`).
- A human-in-the-loop engineering review workflow committing verified answers to reusable memory.

---

## 2. The Three-Frame Architecture

```
SIH26108/
├── frontend/                         # FRAME 1 - React 18, TypeScript, Vite, Tailwind, React Flow
│   ├── src/
│   │   ├── components/
│   │   ├── pages/                   # Dashboard, Search, Upload, Results, Details, Evidence, Graph,
│   │   │                            # Engineer Review, Standards Management, Pre-Publish Validation
│   │   ├── layouts/                 # Navbar with Live Health & Demo Data ribbon
│   │   ├── services/                # Axios API client (api.ts)
│   │   └── types/                   # TypeScript interfaces and DTOs
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                          # FRAME 2 - FastAPI, Pydantic v2, SQLAlchemy
│   ├── app/
│   │   ├── main.py                  # FastAPI Application & Health Check
│   │   ├── api/routes/              # search, upload, recommendations, standards, evidence, graph,
│   │   │                            # review, standards_management, reports, validation
│   │   ├── models/                  # SQLAlchemy ORM (11 entities)
│   │   ├── schemas/                 # Pydantic v2 request/response DTOs
│   │   ├── services/                # query_memory.py (Verified Knowledge Memory)
│   │   └── core/                    # Config & Database Session Management (database.py)
│   ├── requirements.txt
│   └── sih_standards_dev.db         # SQLite local database
│
├── ai_engine/                        # FRAME 3 - AI, Retrieval, Verification & Validation Engine
│   ├── query/                       # query_analyzer.py, rule_extractor.py, llm_provider.py, multilingual.py
│   ├── search/                      # search_engine.py
│   ├── documents/                   # pdf_parser.py, text_extractor.py, chunker.py, document_ingestion_service.py
│   ├── embeddings/                  # embedding_service.py (BGE-M3 & 384-d hashing fallback)
│   ├── vector_db/                   # qdrant_service.py (Qdrant & In-Memory fallback)
│   ├── reranker/                    # reranker.py (4-factor heuristic & constraint verification)
│   ├── knowledge_graph/             # neo4j_service.py & graph_builder.py
│   ├── compliance/                  # compliance_engine.py (QCOs & Make-in-India precedence)
│   ├── verification/                # evidence_verifier.py (Audited page/clause citations)
│   ├── recommendation/              # recommendation_generator.py
│   ├── validation/                  # tender_validator.py (Feature M10: Pre-Publish Audit Rules A-E)
│   └── pipeline/                    # recommendation_pipeline.py (Master Coordinator)
│
├── data/
│   ├── raw/                         # Raw uploaded PDFs & tender text files
│   ├── processed/                   # Chunked tokens & normalized clauses
│   ├── cache/                       # Cached vector embeddings
│   ├── mock/                        # Mock demo seed standards
│   └── real/                        # Verified catalogue (standards_catalogue.json & qco_registry.json)
│
├── docs/
│   ├── ARCHITECTURE_FINAL.md        # Core System Architecture & Invariants
│   └── FINAL_DEMO_CHECKLIST.md      # Demo Runbook & Regression Test Suite
│
├── docker-compose.yml                # PostgreSQL, Qdrant, and Neo4j services
├── .env.example                     # Environment configuration template
└── README.md                        # Documentation and run instructions
```

---

## 3. Core Architectural Pipeline

```
       USER QUERY / TENDER DOCUMENT UPLOAD
                       │
                       ▼
            LLM QUERY UNDERSTANDING
            (Google Gemini / Local RuleExtractor)
            - Extracts technical parameters, materials, ratings
            - Detects foreign standards (e.g., ASTM, ISO, BS)
            - DOES NOT generate Indian Standards
                       │
                       ▼
          VERIFIED STANDARDS RETRIEVAL
          (In-Memory Cosine Vector Store + Fuzzy Lexical Search)
          - Scored against 21 verified BIS catalogue records
          - Checks Query Memory for prior Engineer Approvals
                       │
                       ▼
          STATUTORY COMPLIANCE & QCO RULES
          (QCO Registry + Make-in-India Statutory Precedence)
          - Validates mandatory Quality Control Orders
          - Issues Statutory Precedence Warning for foreign standards
          - Maps certification schemes (Scheme I / BIS Mark)
                       │
                       ▼
          EVIDENCE GROUNDING & AUDIT TRAIL
          - Clause-level text extraction from official scopes
          - Page and section citations
          - Grounding confidence scores
                       │
                       ▼
            ENGINEER REVIEW WORKFLOW
            (APPROVE / MODIFY / REJECT)
            - Engineer remains the final authority
            - Immutable audit trail
                       │
                       ▼
           VERIFIED KNOWLEDGE MEMORY
          - Reusable memory for subsequent identical/similar queries
          - Status re-checked against active catalogue
```

---

## 4. Fundamental Architectural Invariants

### Invariant 1: LLM is NOT the Source of Truth
- The Large Language Model (Google Gemini `gemini-2.5-flash` or local rule-based extractor) is used **exclusively for query comprehension and parameter parsing**.
- The LLM extracts:
  - Equipment / Product name
  - Capacity & Ratings (e.g., 500 kVA, 1100 V, 11 kV)
  - Operating conditions & Cooling methods
  - Construction materials (e.g., PVC, Copper, Fe 500)
  - Foreign standards cited in user tenders (e.g., ASTM, DIN, IEC)
- **The LLM is strictly prohibited from hallucinating or inventing Indian Standards (IS numbers)**.
- All Indian Standards numbers, titles, amendments, and normative references originate strictly from the verified catalogue (`data/real/standards_catalogue.json`).

### Invariant 2: Verified Standards Data is the Single Source of Truth
- All retrieval matches occur against the curated Bureau of Indian Standards dataset.
- Never fabricate:
  - IS numbers or part numbers
  - Quality Control Orders (QCO)
  - Certification schemes
  - Normative and supersede relationships
  - Lifecycle statuses (Active / Superseded / Withdrawn)
- When data is not present in the verified dataset, the system returns `null` or empty arrays rather than guessing.

### Invariant 3: Engineer Remains the Final Decision-Maker
- Automated AI recommendations provide rapid decision support, but the technical engineer holds final approval authority.
- The three supported engineer review decisions:
  1. **APPROVE**: Confirms the recommendation as technically sound. Commits the question-answer pair into persistent **Verified Knowledge Memory**.
  2. **MODIFY**: Allows the engineer to amend primary or related standards without mutating the original source catalogue. Stores both the original AI recommendation and modified version. Status becomes `MODIFIED` and is eligible for verified memory reuse.
  3. **REJECT**: Rejects the AI recommendation with justification comments. Retains the audit record in review history, but **strictly bars the rejected recommendation from being reused as verified memory**.

---

## 5. Detailed Component Architecture

### 5.1 LLM Understanding & Resilient Fallback Layer
- **Primary LLM**: Google Gemini API via `google.genai` Client.
- **Failover Mechanism**: If Gemini encounters HTTP 429 (Rate Limit), HTTP 503, connection timeouts, or missing API keys, the pipeline intercepts the error without bubbling it up to the user or crashing the server.
- **Local RuleExtractor**: Uses regex patterns, domain-specific vocabularies, and keyword dictionaries to extract parameters deterministically when offline.

### 5.2 Retrieval & Embedding Layer
- **Runtime Mode**: `EMBEDDING_PROVIDER=fallback`, `retrieval_mode=IN_MEMORY`.
- **Demo Fallback Embeddings**: 384-dimensional deterministic hashed embeddings providing sub-millisecond query indexing without heavy PyTorch GPU dependencies or out-of-memory crashes.
- **Hybrid Retrieval**: Combines semantic cosine similarity with lexical token matching and mandatory keyword bonuses for unmatched accuracy on technical procurement terminology.

### 5.3 Query Memory Service (Verified Knowledge Loop)
- Before executing vector search, the engine checks `QueryMemoryService` for prior engineer-reviewed sessions matching the query.
- When an exact or high-confidence normalized match is found:
  1. The primary standard's current lifecycle status is re-verified against the active database.
  2. If the standard is still `Active`, the pre-verified answer is surfaced with a **Verified Knowledge Match** badge.
  3. If superseded, the system falls back to a live search, flagging the newer superseding standard.

### 5.4 Statutory Compliance & Foreign Standard Precedence
- Under Public Procurement (Preference to Make in India) Orders and Ministry QCO notifications:
  - If a tender specifies a foreign standard (e.g., `ASTM A36`), the system issues an explicit statutory warning: *"Under Public Procurement (Preference to Make in India) Orders, Indian Standard (IS 2062:2011) takes statutory precedence."*
  - Mandatory QCO items are flagged with red enforcement badges and scheme markings.

### 5.5 Audit-Grade Reporting
- Endpoint: `GET /api/reports/{recommendation_id}` (JSON / HTML print / File download).
- Generates official compliance reports covering 15 audit dimensions, suitable for public procurement audits, technical tender documentation, and purchase committee records.

---

## 6. Stability & Deployment Freeze

| Parameter | Configuration | Justification |
|---|---|---|
| `EMBEDDING_PROVIDER` | `fallback` | Zero memory overhead, instantaneous startup, 100% deterministic |
| `retrieval_mode` | `IN_MEMORY` | Zero external service dependencies (no Qdrant daemon required) |
| `graph_mode` | `IN_MEMORY` | Zero external database dependencies (no Neo4j bolt required) |
| `database` | `SQLite` (`sih_standards_dev.db`) | ACID-compliant, self-contained local storage |
| `frontend` | `React 18 + Vite + TypeScript` | Production build passes with 0 errors |

---

## 7. System Startup Commands & Runtime Runbook

### Backend Server (FastAPI on Port 8000)
```powershell
cd "E:\project 1"
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
- API Root: `http://localhost:8000`
- Interactive Swagger API Docs: `http://localhost:8000/docs`
- System Health: `http://localhost:8000/api/health`

### Frontend Server (React + Vite on Port 5173)
```powershell
cd "E:\project 1\frontend"
npm run dev
```
- Web Application: `http://localhost:5173`

---

## 8. Health & Status Verification

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

## 9. Sample Demo Queries & Expected Results

| # | Procurement Query | Expected Primary Standard | Verification Notes |
|---|---|---|---|
| 1 | `Heavy duty armoured PVC electric cables up to 1100 V` | **IS 1554 (Part 1):1988** | Active, Mandatory QCO Enforced, Clause grounded evidence |
| 2 | `500 kVA outdoor oil cooled distribution transformer 11 kV/433 V` | **IS 1180 (Part 1):2014** / **IS 2026** | Verified electrical power distribution standards |
| 3 | `Structural steel high strength deformed bars for concrete reinforcement Fe 500` | **IS 1786:2008** | Steel reinforcement, QCO mandatory marking |
| 4 | `Plain and reinforced concrete construction works` | **IS 456:2000** | Code of practice for plain and reinforced concrete |

---

## 10. End-to-End Workflow Verification Steps

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

## 11. Known Resilient Fallback Behaviors

| Component | Normal Provider | Fallback Behavior |
|---|---|---|
| **LLM Query Understanding** | Google Gemini (`gemini-2.5-flash`) | Automatic fallback to local regex/keyword `RuleExtractor` on 429/503/timeout. Pipeline never crashes. |
| **Embeddings** | Real BGE-M3 (Heavy) | `DEMO_FALLBACK` (384-d normalized hashing embeddings) runs 100% locally with 0MB external RAM overhead. |
| **Vector DB** | Qdrant | In-Memory Cosine Vector Store with zero external dependencies. |
| **Knowledge Graph** | Neo4j Bolt | In-Memory Graph Index for normative and supersede relationships. |

---

## 12. Regression Testing Suite

Run all verification scripts to validate system integrity:

```powershell
python scripts/verify_phase2.py          # 45/45 Passed
python scripts/verify_phase3.py          # 16/16 Passed
python scripts/verify_phase4.py          # 30/30 Passed
python scripts/verify_phase6a.py         # 62/62 Passed
python scripts/verify_prepublish.py       # 10/10 Passed
python scripts/verify_system.py          # 5/5 Passed
python scripts/verify_real_demo_tests.py # 7/7 Passed (100%)
```

### Frontend Build Check
```powershell
cd "E:\project 1\frontend"
npm run build
```
*(Outputs 0 TypeScript errors).*
