# System Architecture: SIH26108

**AI-Powered Recommendation Engine for Identifying Applicable Indian Standards for Procurement Specifications**  
**Final Production Release Architecture & Core Principles**

---

## 1. Core Architectural Pipeline

The system enforces a strict multi-tier, verifiable pipeline to guarantee that recommendations are factual, grounded in official standards, and compliant with statutory public procurement laws.

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

## 2. Fundamental Architectural Invariants

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

## 3. Detailed Component Architecture

### 3.1 LLM Understanding & Resilient Fallback Layer
- **Primary LLM**: Google Gemini API via `google.genai` Client.
- **Failover Mechanism**: If Gemini encounters HTTP 429 (Rate Limit), HTTP 503, connection timeouts, or missing API keys, the pipeline intercepts the error without bubbling it up to the user or crashing the server.
- **Local RuleExtractor**: Uses regex patterns, domain-specific vocabularies, and keyword dictionaries to extract parameters deterministically when offline.

### 3.2 Retrieval & Embedding Layer
- **Runtime Mode**: `EMBEDDING_PROVIDER=fallback`, `retrieval_mode=IN_MEMORY`.
- **Demo Fallback Embeddings**: 384-dimensional deterministic hashed embeddings providing sub-millisecond query indexing without heavy PyTorch GPU dependencies or out-of-memory crashes.
- **Hybrid Retrieval**: Combines semantic cosine similarity with lexical token matching and mandatory keyword bonuses for unmatched accuracy on technical procurement terminology.

### 3.3 Query Memory Service (Verified Knowledge Loop)
- Before executing vector search, the engine checks `QueryMemoryService` for prior engineer-reviewed sessions matching the query.
- When an exact or high-confidence normalized match is found:
  1. The primary standard's current lifecycle status is re-verified against the active database.
  2. If the standard is still `Active`, the pre-verified answer is surfaced with a **Verified Knowledge Match** badge.
  3. If superseded, the system falls back to a live search, flagging the newer superseding standard.

### 3.4 Statutory Compliance & Foreign Standard Precedence
- Under Public Procurement (Preference to Make in India) Orders and Ministry QCO notifications:
  - If a tender specifies a foreign standard (e.g., `ASTM A36`), the system issues an explicit statutory warning: *"Under Public Procurement (Preference to Make in India) Orders, Indian Standard (IS 2062:2011) takes statutory precedence."*
  - Mandatory QCO items are flagged with red enforcement badges and scheme markings.

### 3.5 Audit-Grade Reporting
- Endpoint: `GET /api/reports/{recommendation_id}` (JSON / HTML print / File download).
- Generates official compliance reports covering 15 audit dimensions, suitable for public procurement audits, technical tender documentation, and purchase committee records.

---

## 4. Stability & Deployment Freeze

| Parameter | Configuration | Justification |
|---|---|---|
| `EMBEDDING_PROVIDER` | `fallback` | Zero memory overhead, instantaneous startup, 100% deterministic |
| `retrieval_mode` | `IN_MEMORY` | Zero external service dependencies (no Qdrant daemon required) |
| `graph_mode` | `IN_MEMORY` | Zero external database dependencies (no Neo4j bolt required) |
| `database` | `SQLite` (`sih_standards_dev.db`) | ACID-compliant, self-contained local storage |
| `frontend` | `React 18 + Vite + TypeScript` | Production build passes with 0 errors |
