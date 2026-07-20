# PlantMind — Industrial Knowledge Assistant

**Problem Statement 8: Industrial Knowledge Intelligence**

A RAG-powered, unified knowledge system that combines equipment manuals and maintenance history into a single searchable knowledge base for field technicians and engineers — so instead of digging through scattered PDFs and paper logs, a technician can just ask a question and get a grounded, cited answer.

🔗 **Live app:** https://plantmind-tqxfegswc6ffifkrga5hvv.streamlit.app/

---

## The Problem

Field technicians deal with knowledge scattered across many sources: OEM manuals, datasheets, past maintenance logs, inspection reports, and tribal knowledge. Critically, these questions are often *relational*, not just informational — "what's failed on this pump before, and is it connected to the motor that also failed last month?" A plain document search can't answer that. PlantMind's design goal was to combine the authoritative knowledge in manuals with the operational history in maintenance logs, and to preserve the *relationships* between assets (e.g., a motor driving a pump) so the system can answer both "how does this work" and "what has actually happened" questions — together.

---

## Architecture

PlantMind uses a **lightweight hybrid RAG** approach rather than a dedicated graph database (e.g. Neo4j):

- **One vector store (ChromaDB)** holds embedded chunks from both equipment manuals and maintenance work orders.
- **Relationship metadata** is attached to every chunk (`asset_id`, `asset_type`, `related_asset_ids`, `failure_mode`, `source_type`, `page_number`) — this metadata layer acts as a lightweight "knowledge graph," letting the system filter and cross-reference by asset relationships without the overhead of standing up a separate graph database.
- **Hybrid retrieval**: instead of a single similarity search over all chunks, each query runs two parallel searches — one filtered to `source_type = "manual"`, one filtered to `source_type = "work_order"` — and merges the results. This ensures answers draw on *both* official documentation and real-world incident history, rather than one dominating the other by sheer chunk volume.

This design was chosen deliberately over a true graph database: at this data scale (23 assets, ~565 chunks), a dedicated graph DB's main advantage — complex multi-hop traversal at scale — isn't the bottleneck, while the hybrid approach is faster to build, easier to iterate on, and still demonstrates genuine relational reasoning.

### Pipeline

```
PDF Manuals (12)  ─┐
                    ├─→ Text Extraction (pdfplumber) → Cleaning (watermark/junk removal)
Work Order Logs ────┤        → Chunking → Metadata Tagging → Embedding (MiniLM) → ChromaDB
(388 synthetic)     │
Asset Registry ─────┘ (defines equipment hierarchy & relationships)
                              ↓
                    Hybrid Retrieval (manual + work_order, merged)
                              ↓
                    Groq LLM (Llama 3.3 70B) generates grounded, cited answer
                              ↓
                    Streamlit Chat Interface (with source citations)
```

---

## Data Sources

| Source | Description | Volume |
|---|---|---|
| Equipment manuals | Real OEM manuals/datasheets (Flowserve, Grundfos, Siemens, York, etc.) covering 12 equipment types | 12 PDFs, 240 pages |
| Asset registry | Custom-built registry mapping 23 individual assets to 12 equipment types, with parent-child relationships (e.g. motor → pump it drives) | 23 assets |
| Maintenance work orders | Synthetically generated logs grounded in realistic failure modes per equipment type, with randomized technical detail (measurements, part numbers, technician notes) and cross-asset references | 388 work orders |
| AI4I 2020 Predictive Maintenance Dataset | Real structured sensor/failure dataset (Kaggle) used to ground synthetic failure-mode patterns in realistic data | Reference dataset |

**Why synthetic work orders?** Real CMMS/maintenance log data is proprietary and not publicly available. Synthetic logs were generated with a custom Python script using template + randomized-placeholder generation (not LLM-per-row, for speed and reproducibility), iteratively refined to eliminate exact-duplicate root causes/actions and ensure technical consistency between failure mode, root cause, action taken, and parts used.

---

## Tech Stack

- **PDF parsing:** `pdfplumber`
- **Embeddings:** `sentence-transformers` (`all-MiniLM-L6-v2`) — free, local, no API key required
- **Vector store:** `ChromaDB` (persistent local client)
- **LLM (answer generation):** Groq API, `llama-3.3-70b-versatile` (free tier)
- **Interface:** Streamlit
- **Data generation & processing:** `pandas`, `openpyxl`, Python `random`

---

## Knowledge Base Stats

- **Total chunks:** 565
- **Manual chunks:** 177 (after filtering ~47 junk/watermark chunks)
- **Work order chunks:** 388
- **Equipment types covered:** 12 (pumps, motors, compressors, dryers, chillers, cooling towers, transformers, distribution panels, boilers, conveyors)
- **Assets tracked:** 23, with mapped parent-child relationships

---

## Example Queries

- *"What maintenance history does PUMP-101 have?"* → pulls specific, cited work order history
- *"Is there a connection between motor bearing failures and the pumps they drive?"* → demonstrates cross-asset relational reasoning
- *"What should I check if a steam boiler is making popping sounds?"* → pulls manual-based troubleshooting content
- *"What causes cavitation in centrifugal pumps?"* → in cases where retrieved context is insufficient, the system correctly declines to answer rather than hallucinating — an intentional design choice for a domain where incorrect information carries real safety/operational risk

---

## Known Limitations

- **PDF text extraction artifacts:** Some manual pages (particularly tables and multi-column layouts) lose whitespace during extraction (e.g. "Insufficientflowrate"), which can slightly reduce retrieval relevance for content on those specific pages. A future improvement would use layout-aware parsing or OCR-based extraction for these sections.
- **Synthetic data:** Maintenance logs are synthetically generated rather than sourced from a real plant, since real CMMS data is proprietary. Failure modes, technical detail, and language variation were designed to closely mirror realistic technician field notes, but some patterns may not perfectly reflect real-world maintenance record-keeping.
- **No image/diagram understanding:** P&IDs, schematics, and embedded diagrams are not processed — this was scoped out as a stretch goal given project timeline, in favor of robust text-based retrieval.
- **Lightweight graph, not a true graph database:** Relationships are represented via metadata filtering rather than a dedicated graph database (e.g. Neo4j). This was a deliberate architectural tradeoff for build speed at this data scale; a production system with more assets and deeper multi-hop relationship needs would benefit from a true graph database.

---

## Running Locally

```bash
# Clone the repo
git clone <repo-url>
cd document-brain

# Set up virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Set your Groq API key (free tier: console.groq.com)
$env:GROQ_API_KEY="your_key_here"

# Run the app
streamlit run app.py
```

To regenerate the knowledge base from scratch (ingest manuals + work orders into ChromaDB), run the cells in `plantmind_ingestion.ipynb` in order.

To regenerate synthetic maintenance logs:
```bash
python generate_synthetic_logs.py
```

---

## Project Structure

```
document-brain/
├── app.py                          # Streamlit chat interface
├── generate_synthetic_logs.py      # Synthetic work order generator
├── plantmind_ingestion.ipynb       # Ingestion pipeline (PDF → chunks → embeddings → ChromaDB)
├── requirements.txt
├── data/
│   ├── asset_registry.xlsx         # Asset hierarchy & relationships
│   ├── manuals/                    # 12 equipment manual PDFs
│   ├── synthetic_logs/             # Generated work order CSVs
│   └── structured/                 # AI4I 2020 reference dataset
└── chroma_db/                      # Persistent vector store
```