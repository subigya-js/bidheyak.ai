# Bidheyak.ai

An **agentic AI chatbot** for querying and analyzing bills from the
[House of Representatives of Nepal](https://hr.parliament.gov.np/en).
Bill documents are published as Nepali-language PDFs; Bidheyak.ai ingests
them, makes them searchable, and answers questions in Nepali or English —
retrieving the relevant legislation and reasoning across multiple bills to
respond, rather than answering from a single lookup.

> **Bidheyak** (विधेयक) is the Nepali word for *bill* (proposed legislation).

## How it works

The system has two independent halves that share **only** a database — they
never import each other's code.

1. **Ingestion** (`ingestion/`) — runs offline on a schedule. Scrapes the
   bills, extracts Nepali text from the PDFs (handling legacy Preeti fonts
   and scanned documents via OCR), splits the text into chunks, embeds them
   into vectors, and stores them in the database.
2. **Web** (`web/`) — the live Next.js chat app. When a user asks a question,
   it embeds the question, retrieves the most relevant chunks from the
   database, and asks an LLM to answer using that retrieved context.

```
User question
  → embed question
    → retrieve matching bill chunks from the vector database
      → LLM answers, grounded in the retrieved text, with a citation
```

## Tech stack

| Concern            | Choice                                  | Notes                                      |
| ------------------ | --------------------------------------- | ------------------------------------------ |
| Scraping           | Python (Playwright / requests)          | Handles paginated bill listings            |
| PDF text           | PyMuPDF                                 | For PDFs with a real text layer            |
| OCR (scanned PDFs) | EasyOCR (Google Cloud Vision fallback)  | Devanagari script support                  |
| Legacy fonts       | Preeti → Unicode conversion             | Many gov PDFs are not real Unicode         |
| Embeddings         | BGE-M3 (self-hosted)                    | Multilingual, cross-lingual retrieval      |
| Reranker (Phase 2) | BGE reranker (self-hosted)              | Improves retrieval precision               |
| Vector database    | Postgres + pgvector (Supabase / Neon)   | Vectors plus metadata filtering            |
| Web App framework  | Next.js + Vercel AI SDK                 | Streaming chat UI and tool calls           |
| LLM                | OpenAI (via OpenRouter later)           | Swap models with a config change           |

## Repository structure

```
bidheyak-ai/
├── ingestion/        # offline Python pipeline (scrape → extract → embed → store)
├── web/              # live Next.js chat application
├── eval/             # (Phase 4) retrieval & model evaluation
├── .env.example      # template for required environment variables
└── README.md
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- A hosted Postgres database with the `pgvector` extension (Supabase or Neon)
- An OpenRouter API key

## Setup

### 1. Environment variables

Copy the template and fill in real values. Never commit the real `.env` files.

```bash
cp .env.example
```

### 2. Ingestion (Python)

```bash
cd ingestion
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

This scrapes the bills, processes the PDFs, and writes vectors to the
database. Re-running it is safe — unchanged bills are skipped, and only new
or modified bills are reprocessed.

### 3. Web (Next.js)

```bash
cd web
```

```bash
npm install
```

```bash
npm run dev
```

The app reads from the same database the ingestion pipeline writes to.

## Environment variables

| Variable             | Used by         | Description                                |
| -------------------- | --------------- | ------------------------------------------ |
| `DATABASE_URL`       | ingestion + web | Hosted Postgres connection string          |
| `OPENROUTER_API_KEY` | web             | LLM access via OpenRouter                  |
| `EMBEDDING_URL`      | web             | Endpoint that embeds the user's question   |

> **Important:** the question and the documents must be embedded with the
> **same** model, or retrieval breaks. In development this runs locally on
> your machine; in production the embedding model must be served at a
> reachable endpoint (`EMBEDDING_URL`).

## Deployment

- **Web** → Vercel
- **Database** → Supabase or Neon (free tier is sufficient at this scale)
- **Ingestion** → runs on your machine, or on a scheduled job (e.g. a cron
  GitHub Action) that pushes fresh data to the hosted database

## Build phases

- **Phase 0** — Ingestion: scrape, extract Nepali text, handle Preeti & OCR
- **Phase 1** — Basic RAG: chunk, embed, retrieve, answer with citation
- **Phase 2** — Better retrieval: hybrid search, reranking, metadata filters
- **Phase 3** — Agentic layer: give the LLM tools for multi-step questions
- **Phase 4** — Evaluation: measure retrieval and answer quality

## License

TBD
