# BIS SpecEngine (SIH26108): Complete End-to-End Project Analysis & Technical Report

**Project Title**: AI-Powered Recommendation Engine for Identifying Applicable Indian Standards for Procurement Specifications  
**Hackathon**: Smart India Hackathon 2026 (SIH26108)  
**System Designation**: BIS SpecEngine  
**Version**: 1.0.0 (Production Stable Freeze)  
**Authoritative Source of Truth**: Curated BIS Catalogue (`data/real/standards_catalogue.json`) & QCO Registry (`data/real/qco_registry.json`)

---

## Executive Summary

Procurement officers in Indian public sector undertakings (PSUs), government departments (CPWD, MES, NHAI, RITES), and municipal bodies frequently face severe compliance and audit risks due to incorrectly or ambiguously specified standards in tenders and RFPs. Tenders often cite outdated or superseded Indian Standards, miss mandatory Quality Control Orders (QCOs), specify foreign standards (such as ASTM, DIN, BS, IEC) in violation of statutory Public Procurement (Preference to Make in India) orders, or rely on vague vendor claims.

**BIS SpecEngine** is an evidence-first, auditable, and deterministic decision-support platform designed to solve this problem comprehensively. It decomposes natural language requirements or raw tender documents, identifies applicable Indian Standards, enforces statutory regulatory mandates, cross-references normative and testing relationships via a knowledge graph, provides verbatim clause and page citations, and maintains a human-in-the-loop review workflow that commits engineer approvals to a verified knowledge memory.

---

## 1. System Architecture: The Three-Frame Framework

The project is structured into three cleanly decoupled layers ("Frames"):

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FRAME 1: FRONTEND                               │
│  React 18 + TypeScript + Vite + Tailwind CSS + React Flow (@xyflow)    │
│  - 10 Specialized Pages (Dashboard, Search, Upload, Results, Details,  │
│    Evidence, Knowledge Graph, Engineer Review, Standards Management,   │
│    Pre-Publish Validation)                                             │
│  - Real-time Backend Health Monitor, Demo Mode Ribbon, Dark Theme      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST (Axios)
┌───────────────────────────────────▼────────────────────────────────────┐
│                        FRAME 2: BACKEND                                │
│  FastAPI + SQLAlchemy + Pydantic v2 + SQLite / PostgreSQL              │
│  - 10 REST Route Modules (/api/search, /upload, /recommendations,      │
│    /standards, /evidence, /graph, /review, /reports, /pre-publish,     │
│    /standards/manage)                                                  │
│  - Database Entities: User, Document, DocumentChunk, Standard,         │
│    Recommendation, Evidence, ComplianceRequirement, VerifiedAnswer,    │
│    ReviewRecord, StandardVersionHistory, TenderValidationRecord        │
│  - QueryMemoryService (Verified Knowledge Loop with Status Re-check)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Internal Invocations
┌───────────────────────────────────▼────────────────────────────────────┐
│                        FRAME 3: AI ENGINE                              │
│  Hybrid Intelligence & Deterministic Retrieval Core                    │
│  - Query Analyzer & Multilingual Normalizer (Unicode safe)             │
│  - Google Gemini 2.5 Flash / Local Regex RuleExtractor Fallback        │
│  - Dual Embedding Core: BGE-M3 Dense / 384-d Deterministic Fallback    │
│  - Qdrant Vector Store / In-Memory Cosine Similarity Engine            │
│  - 4-Tier Contextual Re-ranker (Semantic, Material, Environment, Term) │
│  - Hard Constraint Verification (Voltage, Insulation, Category)        │
│  - Statutory Compliance Engine (DPIIT/BIS QCO Registry)                │
│  - Verbatim Evidence Verifier (Page & Clause citations)                │
│  - Knowledge Graph Service (Neo4j Bolt / In-Memory Graph Index)        │
│  - Feature M10: Pre-Publish Tender Validator (5 Deterministic Rules)   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Architectural Invariants & Trust Safeguards

The platform is built on strict engineering invariants designed for government auditability:

1. **The LLM is NOT the Source of Truth**:
   - The Large Language Model (Google Gemini `gemini-2.5-flash`) is used **strictly for natural language query understanding, entity parsing, and parameter extraction**.
   - The LLM is **strictly prohibited from hallucinating or inventing Indian Standard numbers**.
   - If the Gemini API is unavailable (network error, quota exhaustion 429, timeout), the system automatically falls back to the deterministic local `RuleExtractor` without crashing or showing an error.

2. **Verified Standards Data is the Single Source of Truth**:
   - All recommendations originate solely from curated records in `standards_catalogue.json` (21 active/superseded Indian Standards) and `qco_registry.json` (5 statutory QCO mandates).
   - If an item is uncatalogued or has insufficient evidence, the engine explicitly returns 0 recommendations with an advisory note requiring manual officer review.

3. **Engineer Remains the Final Authority (Human-in-the-Loop)**:
   - AI recommendations are strictly advisory. The technical engineer can **Approve**, **Modify**, or **Reject** any recommendation.
   - Approvals and modifications are stored in persistent `VerifiedAnswer` memory and can be reused for subsequent identical queries. Rejections are preserved in audit history but barred from reuse.

4. **Zero-Failure Offline Resilience**:
   - The entire stack runs without external heavy dependencies. In the absence of Docker, PostgreSQL, Qdrant, or Neo4j, the system executes in zero-dependency Dev Mode using SQLite, in-memory cosine vector indexing, and in-memory graph relationships.

---

## 3. End-to-End Query & Retrieval Execution Flow

When a user submits a procurement query (e.g., *"Heavy duty armoured PVC electric cables up to 1100 V"*), the pipeline executes the following 8 stages:

```
[User Query]
     │
     ▼
[Stage 1: Multilingual Detection & Normalization]
     ├─ Detects script (Latin, Devanagari, Tamil, Telugu, etc.)
     └─ Translates/normalizes to canonical English technical terms
     │
     ▼
[Stage 2: Technical Concept & Entity Extraction]
     ├─ LLM Understanding (Gemini) or RuleExtractor
     ├─ Extracts: Product, Voltage, Materials, Environment, Application
     └─ Detects foreign standards (ASTM, IEC, DIN, BS, ISO, IEEE, EN)
     │
     ▼
[Stage 3: Verified Knowledge Memory Check]
     ├─ Checks QueryMemoryService for prior Engineer Approvals
     ├─ Verifies live status: Is standard still Active or Superseded?
     └─ If active match exists -> Instant Verified Knowledge Result
     │
     ▼ (If live retrieval needed)
[Stage 4: Dense Vector Semantic Search]
     ├─ Embeds search query (BGE-M3 or 384-d normalized hashed embedding)
     └─ Queries Qdrant / In-Memory collection `indian_standards` (Top-K)
     │
     ▼
[Stage 5: 4-Factor Contextual Re-ranking & Compatibility Pruning]
     ├─ Weighted score: 40% Semantic + 20% Material + 20% Environment + 20% Term Alignment
     ├─ Hard Voltage Check: Flags/excludes standards whose max voltage < query voltage
     ├─ Hard Insulation Check: Validates PVC vs XLPE match
     └─ Product Category Check: Prunes incompatible categories (e.g., cables vs cement)
     │
     ▼
[Stage 6: Knowledge Graph, Compliance & Evidence Verification]
     ├─ Neo4j / In-Memory Graph: Links normative references & mandatory test methods (IS 10810, IS 516)
     ├─ Compliance Engine: Evaluates mandatory QCOs & Scheme I (ISI Mark)
     ├─ Evidence Verifier: Extracts verbatim scope excerpts, page numbers, and clauses
     └─ Foreign Precedence Engine: Emits Make-in-India statutory conflict warnings
     │
     ▼
[Stage 7: Recommendation Generator & DTO Assembly]
     ├─ Structures primary recommendations, score factors, and related standards
     └─ Populates excluded candidates with explicit reasons and advisory notices
     │
     ▼
[Stage 8: UI Presentation & Audit-Grade Reporting]
     └─ Interactive card, Graph visualizer, Review panel, and 15-Section PDF/HTML Report
```

---

## 4. Comprehensive Feature Breakdown

### 4.1 Frame 1: Frontend User Experience & Pages

The frontend is built with React 18, Vite, and Tailwind CSS. It features 10 fully realized pages and routes:

| Route | Page Component | Primary Features & Capabilities |
|---|---|---|
| `/` | `Dashboard.tsx` | Live operational status banner, system health metrics (Active Standards, Verified Decisions, Pipeline Mode, SQLite status), hero natural-language search bar with 4 quick sample queries, primary navigation cards, and live review activity feed. |
| `/search` | `StandardSearch.tsx` | Full-text and natural language search interface, domain filtering (Electrical, Civil, Waterproofing, Fire Safety), multilingual query handling, AI query understanding card, foreign standard statutory warnings, score factor breakdowns, excluded candidate transparency, and in-line engineer review panel. |
| `/upload` | `UploadTender.tsx` | Drag-and-drop file uploader for `.pdf` and `.txt` procurement specifications (up to 25MB). Displays upload progress, page extraction stats, detected explicit IS codes, text chunk samples, and one-click execution of the recommendation engine. |
| `/results` | `RecommendationResults.tsx` | Detailed recommendation results view. Displays primary standards, active/superseded lifecycle badges, mandatory QCO enforcement banners, normative test methods, score breakdown bars, grounded evidence snippets, interactive engineer review actions (Approve, Modify, Reject), and compliance report export buttons. |
| `/standards/:standardId` | `StandardDetails.tsx` | Dedicated standard registry inspector. Displays full standard title, edition, lifecycle status, official scope text, keywords, compliance schemes, normative references, test methods, and direct link to graph exploration. |
| `/evidence` | `EvidenceViewer.tsx` | Dedicated audit trail viewer. Allows looking up any recommendation session by ID (`rec_...`), displaying verbatim textual extracts, exact source document/catalogue page numbers, clause coordinates, confidence scores, and audit status. |
| `/graph/:standardId?` | `KnowledgeGraphView.tsx` | Interactive node-link graph powered by `@xyflow/react`. Visualizes root standards, normative references (`NORMATIVE_REFERENCE`), test methods (`REQUIRES_TESTING_VIA`), materials (`SPECIFIES_MATERIAL`), and superseding history (`SUPERSEDES`). Includes node click inspector, zoom controls, and standard selector dropdown. |
| `/review` | `EngineerReview.tsx` | Verified Knowledge Management portal. Lists all engineer-reviewed decisions (`APPROVED`, `MODIFIED`, `REJECTED`, `PENDING`), search filter, audit history timestamps, justification notes, and modified standard associations. |
| `/manage` | `StandardsManagement.tsx` | Administrative standards catalogue portal. Allows adding new standards (`POST /api/standards/manage/add`), updating lifecycle status and superseding codes (`PUT /api/standards/manage/{standard_number}`), viewing chronological version history, and triggering live vector re-indexing. |
| `/pre-publish` | `PrePublishValidation.tsx` | Pre-publish tender validation portal (Feature M10). Deterministically audits draft tender specifications against 5 verification rules, displaying a 0-100 overall score, categorized findings (Critical, High, Medium, Low), officer sign-off form, and official downloadable validation reports. |

---

### 4.2 Frame 2: Backend REST API Architecture

The FastAPI backend exposes modular routes under the `/api` prefix:

#### Search & Recommendations
- `POST /api/search`: Accepts `query`, `limit`, and optional `domain_filter`. Decomposes requirements, checks verified memory, performs semantic vector search, re-ranks, verifies evidence, and returns structured recommendations.
- `GET /api/recommendations/{recommendation_id}`: Retrieves cached recommendation results and metadata by session ID.

#### Tender Document Ingestion
- `POST /api/upload`: Handles multipart file upload (`.pdf` or `.txt`), extracts text page-by-page (PyMuPDF / pdfplumber fallback), performs chunking with overlap, scans for explicit IS codes, embeds chunks, and stores them in SQLite and Qdrant.
- `POST /api/analyze-document`: Executes the recommendation pipeline directly against the extracted chunks of an uploaded document ID.

#### Standards Catalogue & Graph
- `GET /api/standards`: Lists all verified standards in the active catalogue.
- `GET /api/standards/{standard_id}`: Fetches complete metadata, scope, and relations for a specific standard.
- `GET /api/standards/{standard_id}/related`: Returns normative references, test methods, and superseding standards.
- `GET /api/graph/{standard_id}`: Returns React Flow-compatible nodes and edges representing the standards relationship network.

#### Engineer Review & Verified Memory Loop
- `POST /api/review/{recommendation_id}/approve`: Commits recommendation as `APPROVED` into `VerifiedAnswer` table with optional comments.
- `POST /api/review/{recommendation_id}/modify`: Allows engineer to amend the primary standard and related standards. Saves as `MODIFIED` in `VerifiedAnswer`.
- `POST /api/review/{recommendation_id}/reject`: Marks recommendation as `REJECTED` with required comment. Retains immutable audit record in `ReviewRecord`, but strictly bars it from future memory reuse.
- `GET /api/review/knowledge`: Queries persistent verified answers with optional status filtering.
- `GET /api/review/history/{recommendation_id}`: Retrieves chronological audit log of all review actions taken on a recommendation.

#### Standards Management & Versioning
- `POST /api/standards/manage/add`: Adds a new Indian Standard to the active database catalogue.
- `PUT /api/standards/manage/{standard_number}`: Updates standard lifecycle status (Active, Superseded, Withdrawn) and logs a `StandardVersionHistory` record.
- `GET /api/standards/manage/versions`: Returns the chronological lifecycle change log.
- `POST /api/standards/manage/reindex`: Re-indexes all catalogue standards into the active vector collection.

#### Audit-Grade Reports
- `GET /api/reports/{recommendation_id}`: Returns the 15-section audit report as JSON or standalone styled printable HTML (`format=html`).
- `GET /api/reports/{recommendation_id}/download`: Serves the report as a downloadable HTML file for official tender records.

#### Pre-Publish Tender Validation (Feature M10)
- `POST /api/pre-publish/validate`: Validates raw tender text or an uploaded `document_id` against Rules A through E.
- `GET /api/pre-publish/validate/{validation_id}`: Retrieves stored validation report by ID.
- `POST /api/pre-publish/validate/{validation_id}/review`: Records the responsible procurement officer's sign-off decision (`APPROVED_FOR_PUBLICATION`, `APPROVED_WITH_NOTES`, `RETURNED_FOR_REVISION`, `REJECTED`).
- `GET /api/pre-publish/validate/{validation_id}/download`: Downloads the official pre-publish validation certificate/report in printable HTML format.

#### System Health
- `GET /api/health`: Real-time operational diagnostics checking database connectivity, Qdrant vector store status, Neo4j connectivity, retrieval mode, and active embedding provider.

---

### 4.3 Frame 3: AI Engine & Intelligence Components

#### 1. Query Analyzer (`ai_engine/query/query_analyzer.py`)
- Coordinates query processing across scripts and languages.
- Integrates `MultilingualNormalizer` to detect Devanagari, Tamil, Latin, etc., and produce clean English technical terminology.
- Dispatches query to `LLMProvider` (Google Gemini) for structured parsing, or to `RuleExtractor` if offline.
- Identifies technical domains (Electrical, Waterproofing, Civil, Fire Safety) and extracts candidate entity tokens.

#### 2. Local Rule-Based Extractor (`ai_engine/query/rule_extractor.py`)
- Deterministic regex and vocabulary engine supporting robust offline execution.
- Extracts product names, operating voltages (converts kV to Volts), conductor materials (Copper, Aluminium), insulation materials (PVC, XLPE), duty types (heavy-duty, light-duty), and foreign standard citations (ASTM, IEC, DIN, BS, EN, ISO, IEEE).

#### 3. Search Engine & Embeddings (`ai_engine/search/search_engine.py`, `ai_engine/embeddings/embedding_service.py`)
- Provides dense semantic retrieval over standards catalogue and tender chunks.
- Supports dual embedding modes:
  - **BGE-M3 Dense Embeddings**: 1024-dimensional multilingual embeddings.
  - **Demo Fallback Embeddings**: 384-dimensional normalized hashed vectors running with 0MB external RAM and sub-millisecond latency.
- Manages dual Qdrant collections: `indian_standards` (standards catalogue) and `tender_chunks` (uploaded document passages).

#### 4. Contextual Re-ranker (`ai_engine/reranker/reranker.py`)
- Computes a transparent, 4-factor weighted score:
  $$\text{Final Score} = 0.40 \times S_{\text{semantic}} + 0.20 \times S_{\text{material}} + 0.20 \times S_{\text{environment}} + 0.20 \times S_{\text{alignment}}$$
- Enforces **hard domain compatibility constraints**:
  - **Voltage Conflict**: If query specifies $1100\text{ V}$, standards rated only up to $450/750\text{ V}$ (such as `IS 694`) are excluded as direct matches and flagged with `EXCLUDED_VOLTAGE_CONFLICT`.
  - **Insulation Conflict**: If query specifies XLPE, PVC-only standards are flagged.
  - **Category Conflict**: Transformer or cement queries will not match cable standards.

#### 5. Compliance & Statutory Engine (`ai_engine/compliance/compliance_engine.py`)
- Cross-references candidate standards against `data/real/qco_registry.json`.
- Enforces mandatory certification schemes (e.g., BIS Product Certification Scheme I, Schedule II, ISI Mark).
- Identifies statutory Make-in-India precedence over cited foreign standards (e.g., `ASTM A36` $\rightarrow$ `IS 2062:2011`).

#### 6. Evidence Verifier (`ai_engine/verification/evidence_verifier.py`)
- Grounding engine that enforces verifiable citations.
- Extracts matching text excerpts with page and clause coordinates from uploaded chunks or official catalogue scope definitions.
- If a recommendation lacks empirical textual support, it strictly returns `"Insufficient evidence"` rather than generating synthetic text.

#### 7. Knowledge Graph Service (`ai_engine/knowledge_graph/neo4j_service.py`, `graph_builder.py`)
- Models relationships between standards:
  - `REQUIRES_TESTING_VIA`: Links cable standards (e.g., `IS 694`, `IS 1554`) to test code `IS 10810`, and concrete standards (`IS 456`) to `IS 516`.
  - `SPECIFIES_MATERIAL`: Links `IS 456` to aggregate specification `IS 383`.
  - `SUPERSEDES`: Links modern revisions to superseded standards (e.g., `IS 456:2000` $\rightarrow$ `IS 456:1978`).
- Operates seamlessly with Neo4j Bolt connection or in-memory graph index fallback.

#### 8. Pre-Publish Tender Validator (`ai_engine/validation/tender_validator.py`)
- Feature M10 audit engine evaluating draft tenders against 5 deterministic rules:
  - **Rule A (Superseded Standards)**: Flags citations of obsolete standards (e.g., `IS 456:1978`) and identifies the active replacement (`IS 456:2000`). Severity: `CRITICAL`.
  - **Rule B (Mandatory QCO Verification)**: Checks whether specified items are governed by mandatory Quality Control Orders and verifies if mandatory ISI mark requirements are explicitly stated. Severity: `HIGH`.
  - **Rule C (Foreign Standards Precedence)**: Detects foreign codes (`ASTM`, `IEC`, `DIN`, `BS`, `EN`) and alerts the officer to evaluate Indian Standard equivalence under Make-in-India rules. Severity: `MEDIUM`.
  - **Rule D (Normative & Test Method Consistency)**: Verifies if mandatory testing standards (e.g., `IS 516`, `IS 10810`, `IS 2386`) are properly cited alongside the product standards. Severity: `LOW`.
  - **Rule E (Evidence Grounding & Completeness)**: Validates that all cited standards exist in verified records and have verifiable clause scopes.
- Computes an overall compliance score ($0 - 100$) and generates an executive audit summary.

---

## 5. Curated Indian Standards Catalogue & Dataset Summary

The system is seeded with 21 verified Bureau of Indian Standards specifications across electrical, civil, and mechanical procurement domains:

| Standard Number | Title | Status | Supersedes | Key Relationships / Test Methods |
|---|---|---|---|---|
| **IS 456:2000** | Plain and Reinforced Concrete - Code of Practice | Active | IS 456:1978 | Specifies `IS 383:2016`, Test via `IS 516:1959` |
| **IS 800:2007** | General Construction in Steel - Code of Practice | Active | IS 800:1984 | Structural design & erection guidelines |
| **IS 383:2016** | Coarse and Fine Aggregate for Concrete | Active | IS 383:1970 | Test via `IS 2386 (Part 1):1963` |
| **IS 1786:2008** | High Strength Deformed Steel Bars (TMT) for Concrete | Active | IS 1786:1985 | Reinforcement steel, QCO covered |
| **IS 2062:2011** | Hot Rolled Medium and High Tensile Structural Steel | Active | IS 2062:2006 | Make-in-India precedence over ASTM A36 |
| **IS 694:2010** | PVC Insulated Cables for Working Voltages up to 1100V (Domestic/Building) | Active | IS 694:1990 | Mandatory QCO (ISI Mark), Test via `IS 10810` |
| **IS 1554 (Part 1):1988** | Heavy Duty Armoured PVC Cables up to 1100V | Active | IS 1554:1976 | Mandatory QCO (ISI Mark), Test via `IS 10810` |
| **IS 7098 (Part 1):1988** | Crosslinked Polyethylene (XLPE) Insulated Cables up to 1100V | Active | IS 7098:1977 | Mandatory QCO (ISI Mark), Test via `IS 10810` |
| **IS 732:2019** | Electrical Wiring Installations - Code of Practice | Active | IS 732:1989 | Wiring safety & installation code |
| **IS 269:2015** | Ordinary Portland Cement - Specification | Active | IS 269:1989 | Mandatory QCO (Cement Control Order) |
| **IS 1489 (Part 1):2015** | Portland Pozzolana Cement (Fly Ash Based) | Active | IS 1489:1991 | Mandatory QCO (Cement Control Order) |
| **IS 1239 (Part 1):2004** | Steel Tubes, Tubulars and Other Wrought Steel Fittings | Active | IS 1239:1990 | Water, gas, steam piping |
| **IS 4984:2016** | High Density Polyethylene (HDPE) Pipes for Water Supply | Active | IS 4984:1995 | Potable water distribution |
| **IS 4985:2021** | Unplasticized PVC Pipes for Potable Water Supplies | Active | IS 4985:2000 | Potable water supply networks |
| **IS 1363 (Part 1):2019** | Hexagon Head Bolts, Screws and Nuts (Grade C) | Active | IS 1363:2002 | Mechanical fasteners |
| **IS 1367 (Part 1):2014** | Technical Supply Conditions for Threaded Fasteners | Active | IS 1367:2002 | General fastener specifications |
| **IS 10810 (Series)** | Methods of Test for Cables | Active | - | Normative test suite for IS 694 / IS 1554 |
| **IS 516:1959** | Method of Tests for Strength of Concrete | Active | - | Mandatory test method for IS 456 |
| **IS 2386 (Series)** | Methods of Test for Aggregates for Concrete | Active | - | Mandatory test method for IS 383 |
| **IS/IEC 60529:2001** | Degrees of Protection Provided by Enclosures (IP Code) | Active | IS 2147:1962 | Ingress protection testing (water/dust) |
| **IS 1200 (Series)** | Method of Measurement of Building and Civil Engineering Works | Active | - | Public works measurement code |

---

## 6. Official 15-Section Compliance Report Specification

The platform generates comprehensive audit-grade reports accessible via `GET /api/reports/{recommendation_id}`:

1. **Procurement Requirement**: Original verbatim query or tender requirement text.
2. **Extracted Technical Requirements**: Structured parameters (product, capacity, voltage, materials, environment).
3. **Primary Recommended Indian Standard**: Number, edition, title, and relevance score.
4. **Related Standards**: Additional applicable secondary standards.
5. **Normative References**: Explicit normative references cited within the primary code.
6. **Lifecycle Status**: Active, Superseded, or Withdrawn status.
7. **Last Verified Date**: Timestamp of catalogue verification.
8. **QCO Enforcement Status**: Mandatory QCO order details, gazette notification references.
9. **Applicable Certification Scheme**: Scheme I, ISI Mark, or CRS registration.
10. **Foreign Standard Conflict / Warning**: Statutory Make-in-India precedence notifications.
11. **Compliance Alerts**: Specific regulatory warnings and procurement directives.
12. **Evidence Audit Trail**: Verbatim clauses, page numbers, and section names.
13. **Engineer Review Status**: Status (`APPROVED`, `MODIFIED`, `REJECTED`, or `PENDING`), comments, and review timestamp.
14. **Verification Information**: Verification agency, audit status, and confidence score.
15. **Dataset & Version Information**: Curated dataset version tag (`v1.0-real-21`).

---

## 7. Verification & Regression Testing Results

The system includes a dedicated suite of automated verification scripts located in `scripts/`:

| Verification Script | Scope & Test Focus | Status |
|---|---|---|
| `scripts/verify_phase2.py` | Pipeline stages, vector retrieval, re-ranking, and evidence grounding | **45 / 45 Passed** |
| `scripts/verify_phase3.py` | QCO compliance checks, Make-in-India precedence warnings | **16 / 16 Passed** |
| `scripts/verify_phase4.py` | Engineer review workflow (Approve/Modify/Reject), Query Memory reuse, Standards Management | **30 / 30 Passed** |
| `scripts/verify_phase6a.py` | 15-Section Compliance Reports, HTML export, tender upload pipeline | **62 / 62 Passed** |
| `scripts/verify_prepublish.py` | Feature M10 tender validation rules (Rules A through E), scoring, officer sign-off | **10 / 10 Passed** |
| `scripts/verify_real_demo_tests.py` | Real-world demo procurement queries (Cables, Concrete, Structural Steel, Transformers) | **7 / 7 Passed (100%)** |
| `scripts/verify_system.py` | End-to-end integration health and service coordination | **5 / 5 Passed** |

Frontend compilation check (`npm run build` in `frontend/`) completes with **0 TypeScript errors**.

---

## 8. Operational Runbook & Quick Commands

### Backend Startup
```powershell
cd "E:\project 1"
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/health`

### Frontend Startup
```powershell
cd "E:\project 1\frontend"
npm run dev
```
- Web Application: `http://localhost:5173`

---

## 9. Conclusion

**BIS SpecEngine (SIH26108)** delivers a robust, audit-grade, evidence-first recommendation system that bridges the gap between natural language procurement requirements and statutory Indian Standards. By enforcing that the LLM is never the source of truth, grounding all citations in official catalogue records, enforcing mandatory QCOs and Make-in-India precedence, and empowering technical engineers with final approval authority, the platform provides public procurement authorities with unprecedented confidence, transparency, and compliance assurance.
