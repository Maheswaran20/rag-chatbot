# RAG Chatbot (FastAPI + Streamlit + LangChain)

A free, end-to-end **Retrieval-Augmented Generation (RAG)** chatbot. Ask questions about your own documents (PDF or text) and get answers grounded in their content.

The app has two parts:

- **Backend** — a FastAPI service that does the RAG logic (embed documents, retrieve relevant chunks, ask an LLM to answer). Deployed on **Render**.
- **Frontend** — a Streamlit chat interface. Deployed on **Streamlit Community Cloud**.

Everything runs on **free tiers**: Google Gemini (embeddings), Groq or Gemini (the LLM), and FAISS (local vector store).

---

## How it works (the 30-second version)

```
Your question
   |
   v
Gemini embeds the question into a vector
   |
   v
FAISS finds the most relevant chunks of your document
   |
   v
The LLM (Groq/Gemini) reads those chunks + your question and writes an answer
   |
   v
Answer + sources shown in the Streamlit chat
```

Two different models do two different jobs: the **embedding model** finds the right text, and the **LLM** writes the answer.

---

## Project structure

```
rag-chatbot/
├── backend/
│   ├── main.py              # FastAPI app (the API endpoints)
│   ├── rag.py               # RAG logic: load docs, build index, answer questions
│   ├── requirements.txt     # Backend dependencies (used by Render)
│   ├── runtime.txt          # Pins Python version for Render
│   └── faiss_index/         # Prebuilt vector index (committed to the repo)
├── frontend/
│   ├── app.py               # Streamlit chat UI
│   └── requirements.txt     # Frontend dependencies (used by Streamlit Cloud)
├── data/
│   └── docs/                # Put your PDF / .txt files here
├── .gitignore
└── README.md
```

---

## Prerequisites

Install these first:

- **Python 3.11** (not 3.12+ — some libraries lag behind). Check with `python --version`.
- **Git** — check with `git --version`.
- A code editor such as VS Code.

You also need two free API keys (no credit card required for either):

| Key | Where to get it | Used for |
|-----|-----------------|----------|
| `GOOGLE_API_KEY` | https://aistudio.google.com  → Get API key | Embeddings (and optionally the LLM) |
| `GROQ_API_KEY`   | https://console.groq.com  → API Keys | The LLM (skip if you use Gemini for the LLM) |

---

## Part 1 — Run it locally

### 1. Get the code

```bash
git clone https://github.com/YOUR_USERNAME/rag-chatbot.git
cd rag-chatbot
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv venv
venv\Scripts\activate
```

**Mac / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

You should now see `(venv)` at the start of your prompt. Keep it activated for everything below.

> **Tip:** confirm the venv is really active by running
> `python -c "import sys; print(sys.executable)"`
> The path it prints should include `...\rag-chatbot\venv\...`.

### 3. Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

This takes a few minutes the first time.

### 4. Add your document

Put a PDF or `.txt` file into `data/docs/`. Both formats are supported.

### 5. Set your API keys

**Windows (PowerShell):**

```powershell
$env:GOOGLE_API_KEY="your_google_key_here"
$env:GROQ_API_KEY="your_groq_key_here"
```

**Mac / Linux:**

```bash
export GOOGLE_API_KEY="your_google_key_here"
export GROQ_API_KEY="your_groq_key_here"
```

> These are set for the current terminal session only. If you open a new terminal, set them again. (Alternatively, create a `.env` file in the project root with the same keys — it is loaded automatically and is git-ignored.)

### 6. Build the search index

The index is a snapshot of your document's content. Build it once:

```bash
cd backend
python -c "from rag import build_index_throttled; build_index_throttled()"
```

This reads your document, splits it into chunks, embeds each chunk with Gemini (pausing between batches to respect the free-tier rate limit), and saves a `faiss_index/` folder. Wait for it to print **"Index built"**.

### 7. Run the backend

```bash
uvicorn main:app --reload --port 8000
```

When you see **"Application startup complete"**, open http://localhost:8000/docs — the interactive API page.

**Test it:** expand **POST /ask** → **Try it out** → enter
`{ "question": "What is this document about?" }` → **Execute**.
You should get an answer drawn from your document.

### 8. Run the frontend (in a second terminal)

Open a **new** terminal, activate the venv again, then:

```bash
pip install -r frontend/requirements.txt
cd frontend
streamlit run app.py
```

It opens http://localhost:8501 — your chat interface. Ask a question and you're running the full stack locally.

---

## Part 2 — Deploy it (free)

The backend goes on **Render**, the frontend on **Streamlit Community Cloud**. They deploy separately from the same GitHub repo.

### Step A — Push your code to GitHub

Create an empty repo on GitHub (don't add a README or .gitignore there — you already have them), then:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/rag-chatbot.git
git branch -M main
git push -u origin main
```

> Make sure `.env` is **not** pushed — it should be listed in `.gitignore`. Confirm with `git status` before committing.

### Step B — Deploy the backend on Render

1. Go to https://render.com  and sign up with GitHub.
2. **New +** → **Web Service** → connect your `rag-chatbot` repo.
3. Configure:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
4. Under **Environment**, add these variables:
   - `GOOGLE_API_KEY` = your Google key
   - `GROQ_API_KEY` = your Groq key
   - `PYTHON_VERSION` = `3.11.9`
5. **Create Web Service** and wait for the logs to say **"Your service is live"**.

Your backend URL will look like `https://rag-chatbot-xxxx.onrender.com`. Visit it — you should see `{"status":"ok","message":"RAG API is running"}`.

> **Why the index is committed:** the backend loads the prebuilt `faiss_index/` from the repo instead of rebuilding on startup. This keeps memory low (fits the free tier) and avoids hitting the embedding rate limit. Make sure `faiss_index/` was committed (see the "Updating your document" section).

### Step C — Deploy the frontend on Streamlit Cloud

1. In `frontend/app.py`, set `API_URL` to your live Render URL:
   ```python
   API_URL = "https://rag-chatbot-xxxx.onrender.com"
   ```
   Commit and push this change.
2. Go to https://share.streamlit.io  and sign in with GitHub.
3. **New app** → select your repo → **Branch:** `main` → **Main file path:** `frontend/app.py` → **Deploy**.

You'll get a public URL like `https://your-app.streamlit.app`. That's your shareable chatbot.

---

## Updating your document

When you change the file in `data/docs/`, rebuild the index locally and push it. **Do this locally**, not on the server (rebuilding on the server can hit the free-tier rate limit).

```bash
# from the backend/ folder, with GOOGLE_API_KEY set
# Windows:  Remove-Item -Recurse -Force faiss_index
rm -rf faiss_index
python -c "from rag import build_index_throttled; build_index_throttled()"

cd ..
git add -f backend/faiss_index
git add data/docs
git commit -m "Update source document and index"
git push
```

Render redeploys automatically and loads the new index.

---

## Using Gemini for everything (skip Groq)

If you'd rather use a single provider, you can drop Groq and use Gemini as the LLM too.

In `backend/rag.py`, replace the Groq import and model:

```python
# from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

# llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
```

Then remove `langchain-groq` from `backend/requirements.txt` and delete the `GROQ_API_KEY` variable on Render. Only `GOOGLE_API_KEY` is needed.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError` on import | Wrong package versions installed | Reinstall pinned versions: `pip install -r backend/requirements.txt` |
| pip installs to a global Python path, not the venv | venv not actually active | Recreate: delete `venv`, run `python -m venv venv`, activate, verify with the `sys.executable` check |
| Render build fails on `faiss-cpu==1.8.0` | That version isn't available | The pinned `requirements.txt` already uses a current version |
| Render log still shows Python 3.14 | Version pin not applied | Set `PYTHON_VERSION=3.11.9` in Render's Environment tab |
| `Out of memory (used over 512Mi)` | Running the embedding model in memory | Use Gemini embeddings + committed prebuilt index (as configured) |
| `429 ... quota` / `TooManyRequests` | Too many embedding calls per minute | Build the index locally with `build_index_throttled()`, commit it; don't rebuild on the server |
| `GroqError: api_key ... must be set` | Missing key on Render | Add `GROQ_API_KEY` in Render's Environment tab |
| `DefaultCredentialsError` from Google | Missing key on Render | Add `GOOGLE_API_KEY` in Render's Environment tab |
| First request is very slow | Render free tier sleeps after 15 min idle | Normal — it wakes in 30-60s, then it's fast |

---

## Free-tier limits to keep in mind

- **Render free web service:** sleeps after 15 minutes of inactivity; cold start takes 30-60 seconds. Don't set up auto-pingers to keep it awake — Render may suspend the service for that.
- **Gemini free embeddings:** roughly 100 requests/minute and ~1,000/day. Fine for a learning project. The per-minute limit resets every 60 seconds; the daily limit resets at midnight Pacific (UTC-8).

---

## Tech stack

- **LangChain** — RAG orchestration
- **FastAPI** + **Uvicorn** — backend API
- **Streamlit** — frontend chat UI
- **FAISS** — vector store (local)
- **Google Gemini** — embeddings (and optionally the LLM)
- **Groq (Llama)** — the LLM
- **Render** + **Streamlit Community Cloud** — free hosting
