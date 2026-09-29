# SIH26108: AI-Powered Indian Standards Recommendation Engine

> **Smart India Hackathon 2026**
> **Problem Statement**: SIH26108 – AI-Powered Recommendation Engine for Identifying Applicable Indian Standards for Procurement Specifications.

---

## 1. Project Overview

Procurement officers often struggle to accurately identify the mandatory and applicable Indian Standards (IS) for goods, civil works, and electrical systems specified in tenders and RFPs. 

**BIS SpecEngine** solves this by:
1. **Understanding Queries & Specifications**: Decomposing natural language or tender PDFs into core technical parameters (materials, environments, voltage, safety).
2. **Evidence-First Retrieval**: Matching requirements against Bureau of Indian Standards (BIS) specifications using dense semantic search (Qdrant) and contextual re-ranking.
3. **Auditable Provenance**: Citing exact page and clause numbers from source standards instead of free LLM hallucinations.
4. **Conformity & Regulatory Guidance**: Highlighting mandatory Quality Control Orders (QCOs), BIS Certification schemes (ISI Mark), and Compulsory Registration Schemes (CRS).
5. **Interactive Knowledge Graph**: Visualizing standard relationships (normative references, test methods via `IS 10810`, and superseding codes) via Neo4j and React Flow.

---

## 2. Three-Frame Architecture

```
SIH26108/
├── frontend/                         # FRAME 1 - React, TS, Vite, Tailwind, React Flow
│   ├── src/
│   │   ├── components/
│   │   ├── pages/                   # Dashboard, Search, Upload, Results, Details, Evidence, Graph
│   │   ├── layouts/                 # Navbar with Live Health & Demo Data indicators
│   │   ├── services/                # Axios API client
│   │   └── types/                   # TypeScript DTOs
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                          # FRAME 2 - FastAPI, Pydantic, SQLAlchemy
│   ├── app/
│   │   ├── main.py                  # API App & Health Check
│   │   ├── api/routes/              # search, upload, recommendations, standards, evidence, graph
│   │   ├── models/                  # SQLAlchemy ORM (Document, Standard, Recommendation, Evidence)
│   │   ├── schemas/                 # Pydantic v2 validation DTOs
│   │   └── core/                    # Config & Database Session Management
│   ├── requirements.txt
│   └── .env
│
├── ai_engine/                        # FRAME 3 - AI + Retrieval & Verification Engine
│   ├── query/                       # query_analyzer.py
│   ├── search/                      # search_engine.py
│   ├── documents/                   # pdf_parser.py, text_extractor.py, chunker.py
│   ├── embeddings/                  # embedding_service.py (BGE-M3 / Vector fallback)
│   ├── vector_db/                   # qdrant_service.py (Qdrant + Memory fallback)
│   ├── reranker/                    # reranker.py
│   ├── knowledge_graph/             # neo4j_service.py + graph_builder.py
│   ├── compliance/                  # compliance_engine.py (QCOs & ISI marks)
│   ├── verification/                # evidence_verifier.py (Audited page/clause citations)
│   ├── recommendation/              # recommendation_generator.py
│   └── pipeline/                    # recommendation_pipeline.py (Master Pipeline Coordinator)
│
├── data/
│   ├── raw/                         # Raw uploaded PDFs & tenders
│   ├── processed/                   # Chunked tokens & normalized clauses
│   ├── cache/                       # Cached embeddings
│   └── mock/                        # Curated BIS seed data clearly tagged [DEMO DATA]
│
├── docker-compose.yml                # PostgreSQL, Qdrant, and Neo4j services
├── .env.example                     # Environment configuration template
└── README.md                        # Documentation and run instructions
```

---

## 3. Quick Start Guide

### Prerequisites
- **Node.js**: v20.x or higher
- **Python**: v3.11 or higher
- **Docker** *(Optional for production datastores; the system includes built-in zero-dependency in-memory and SQLite dev fallbacks)*

---

### Step 1: Start the Backend (FastAPI)

1. Open a terminal in the root project directory:
   ```bash
   cd "e:\project 1"
   ```

2. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Launch the FastAPI backend server:
   ```bash
   python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   - API Root: `http://localhost:8000`
   - Interactive Swagger API Docs: `http://localhost:8000/docs`
   - System Health: `http://localhost:8000/api/health`

---

### Step 2: Start the Frontend (Vite + React)

1. In a second terminal, navigate to the `frontend/` directory:
   ```bash
   cd "e:\project 1\frontend"
   ```

2. Install npm dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   - Open your browser at: `http://localhost:5173`

---

### Step 3 (Optional): Launch Production Datastores via Docker

To run full production instances of PostgreSQL, Qdrant, and Neo4j:
```bash
docker compose up -d
```
- **PostgreSQL**: `localhost:5432`
- **Qdrant Vector DB**: `http://localhost:6333/dashboard`
- **Neo4j Browser**: `http://localhost:7474` (User: `neo4j`, Password: `sih_password`)

*Note: If Docker is not running, the application automatically runs in zero-dependency Dev Mode using SQLite and in-memory vector/graph structures with official BIS seed data.*

---

## 4. End-to-End User Flow & Verification

1. **Dashboard (`/`)**:
   - Inspect the live system status ribbon showing active backend connectivity and `DEV / DEMO DATA MODE` badge.
   - Enter a query into the hero search bar or click any sample prompt.
2. **Standard Search (`/search`)**:
   - Enter: `"I need standards for waterproof electrical cables used in buildings"`
   - Click **Recommend**.
   - Observe the returned Indian Standards:
     - `IS 694:2010`: PVC Insulated Cables (Domestic & Building wiring, ISI Mark mandatory under QCO).
     - `IS 1554 (Part 1):1988`: Heavy Duty Armoured PVC Cables (Underground/damp installations).
     - `IS/IEC 60529:2001`: Degrees of Protection Provided by Enclosures (IP Code water test).
     - `IS 732:2019`: Code of Practice for Electrical Wiring Installations (Damp locations).
3. **Inspect Grounded Evidence (`/evidence`)**:
   - Verify that each recommendation specifies exact page numbers and clauses (e.g. *Found on Page 4, Clause 4.2 & Clause 16*).
4. **Knowledge Graph (`/graph`)**:
   - Explore the interactive node graph displaying normative connections and mandatory test method relationships (`REQUIRES_TESTING_VIA` to `IS 10810`).
5. **Upload Tender PDF (`/upload`)**:
   - Upload any procurement tender or technical specification.
   - Verify page-by-page extraction and click **Run AI Recommendation Engine**.

---

## 5. Development & Mock Data Policy

Per SIH guidelines:
- All non-production seed standards are explicitly marked with `[DEMO DATA]` and `is_demo: true`.
- Regulatory claims (QCOs, ISI marks) default strictly to `"Verification required"` unless backed by verified DPIIT / BIS gazette notifications.
- The AI Engine enforces an evidence-first rule: recommendations without grounded excerpts return `"Insufficient evidence"`.
