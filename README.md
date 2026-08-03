<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License MIT">
  <a href="https://github.com/tharunramavath/FastAPI-for-AI-Engineers/actions/workflows/pages.yml"><img src="https://github.com/tharunramavath/FastAPI-for-AI-Engineers/actions/workflows/pages.yml/badge.svg" alt="Pages Deploy"></a>
</p>

<h1 align="center">⚡ FastAPI for AI Engineers</h1>
<h3 align="center">One project. Every pattern. Hands-on.</h3>

<p align="center">
  <strong>Learn FastAPI the way AI engineers actually build with it —</strong><br>
  by building a production-style <em>AI Model Serving API</em> from scratch.<br>
  No GPU. No prior FastAPI knowledge. Just the patterns you'll use every day.
</p>

<br>

---

## 🧭 Two Paths In — Pick Yours

| 🧭 **Hands-On Learning Path** | 📘 **Core Concepts** |
|---|---|
| 13 steps. Read → Run → Observe → Learn. | Diagrams, explanations, interview preparation. |
| Every step tells you **what file to read, what command to run, and what to look for.** | Why each pattern exists and how production AI APIs use it. |
| **[Start the path →](docs/LEARNING_PATH.md)** | **[Read the concepts →](docs/CONCEPTS.md)** |

> 🎯 **Preparing for an AI engineering interview?** [Browse 38 interview questions with answers →](docs/INTERVIEW_QUESTIONS.md) — core concepts, async/streaming, auth, validation, testing, RAG, system design, production, and behavioral questions.

> 🌐 **Prefer a guided browser experience?** [Open the live site →](https://tharunramavath.github.io/FastAPI-for-AI-Engineers/) — cream/red theme, sidebar navigation, scrollspy, search, and resizeable layout.

---

## 🧁 What Makes This Guide Different

Most FastAPI tutorials teach you how to write a single route. This project teaches you how **production AI platforms (OpenAI, Anthropic, Hugging Face) are structured end‑to‑end.**

- **Mocked models** — no GPU required; the concepts are real, the model calls are simulated with realistic latency.
- **Read → Run → Observe → Learn** — every step has executable commands and expected output so you never wonder *"did it work?"*
- **Same patterns used at AI companies** — the auth injection, the SSE streamer, the service layer, the request pipeline.
- **13 passing tests** — an executable correctness baseline you can learn testing from.
- **155MB? No.** — the whole project is a few Python source files, not a massive framework.
- **Zero‑setup Windows/PowerShell support** — curl examples use `curl.exe`, `cp .env.example .env` works, and `.venv\Scripts\activate` is documented.

---

## 🔥 Fire it up (2 minutes)

### 1. Clone
```bash
git clone https://github.com/tharunramavath/FastAPI-for-AI-Engineers.git
cd FastAPI-for-AI-Engineers
```

### 2. Install
```bash
# Create & activate the virtual environment
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install the project dependencies
pip install -r requirements.txt
```

### 3. Configure
```bash
cp .env.example .env          # done — default API key is "test-key-123"
```

### 4. Run
```bash
uvicorn app.main:app --reload
```

### 5. Try It
Open **http://localhost:8000/docs** — every endpoint is documented and interactive right there.

DataReady to glow:
```bash
curl.exe -X POST http://localhost:8000/predict ^
  -H "X-API-Key: test-key-123" ^
  -H "Content-Type: application/json" ^
  -d "{\"text\": \"I'm learning FastAPI by building with it.\", \"model\": \"sentiment\"}"
```

---

## 📍 What You'll Build

A REST API that:

- Accepts text input ↔ runs it through a **model service** (sentiment, LLM, summarizer)
- **Streams tokens** live (Server‑Sent‑Events) like ChatGPT
- Requires **API‑key authentication** via reusable dependency injection
- Attaches **X‑Request‑ID** to every response for tracing
- Uploads images and validates file type / size server‑side
- Publishes model metadata on two levels
- Exposes auto‑generated **Swagger UI** and **ReDoc**
- Handles exceptions centrally and returns consistent JSON errors
- Runs background tasks for billing / logging / metrics

---

## 🗺️ Concepts Covered (at a glance)

| Concept | Where it's taught | Why AI engineers need it |
|---|---|---|
| Path & Query Parameters | `routers/health.py`, `predict.py` | Every inference endpoint uses URL parameters |
| Request Body (Pydantic) | `schemas/request.py` | Validating structured model inputs |
| Response Models | `schemas/response.py` | Structuring model outputs |
| Async / Await | `services/model_service.py` | Model inference is I/O‑intensive — async preserves concurrency |
| Streaming (SSE) | `routers/stream.py` | LLM token streaming |
| Background Tasks | `routers/predict.py` | Post‑inference logging, billing, metrics |
| Dependency Injection | `middleware/auth.py` | Reusable auth, rate limiting, model loading |
| Middleware | `middleware/logging_mw.py` | Request logging, tracing, CORS |
| Exception Handling (global) | `app/main.py` | Clean JSON errors on every failure |
| Lifespan Events | `app/main.py` | Load ML model ONCE at startup |
| File Uploads | `routers/vision.py` | Multimodal / vision model input |
| Router Organisation | `routers/` | Scaling a multi‑model AI platform |
| Env Configuration | `config.py` | API keys, model paths, batch sizes |
| OpenAPI auto‑docs | Zero extra code | Producers can publish API shape to readers |

---

## 📁 Project Structure

```
.
├── app/
│   ├── main.py              ← entry: app, lifespan, middleware, exception handlers
│   ├── config.py            ← typed settings from .env (pydantic-settings)
│   ├── routers/
│   │   ├── predict.py       ← POST /predict, GET /models (query params + background tasks)
│   │   ├── stream.py        ← POST /stream   (SSE token streaming)
│   │   ├── vision.py        ← POST /vision/analyze  (file upload)
│   │   └── health.py        ← GET /health, GET /models/{name} (path params, no auth)
│   ├── schemas/
│   │   ├── request.py       ← Pydantic *input* model schemas
│   │   └── response.py      ← Pydantic *output* model schemas
│   ├── services/
│   │   └── model_service.py ← the core model invokation layer (mocked)
│   └── middleware/
│       ├── auth.py          ← API‑key auth as a reusable dependency
│       └── logging_mw.py    ← request / response logging + X‑Request‑ID
├── tests/
│   └── test_predict.py      ← 13 tests (TestClient + pytest)
├── docs/                    ← ✨ GitHub Pages site (cream/red, sidebar, scrollspy)
│   ├── index.html
│   ├── 404.html
│   ├── assets/
│   │   ├── style.css
│   │   └── app.js
│   ├── LEARNING_PATH.md     ← 13‑step hands‑on walkthrough
│   ├── CONCEPTS.md          ← deep dive concept guide
│   └── MAP.md               ← file‑level project map + cheat‑sheet
├── .github/workflows/
│   └── pages.yml            ← deploy docs/ to GitHub Pages
├── requirements.txt
├── .env.example
└── README.md                ← you are here
```

---

## 🧪 Try These Requests (in order)

```bash
# 1. Health check — no auth needed
curl http://localhost:8000/health

# 2. Predict — requires API‑key header
curl -X POST http://localhost:8000/predict -H "X-API-Key: test-key-123" -H "Content-Type: application/json" ^
  -d "{\"text\": \"I love this product\", \"model\": \"sentiment\", \"max_tokens\": 100}"

# 3. Stream tokens — each one arrives one at a time
curl -N -X POST http://localhost:8000/stream -H "X-API-Key: test-key-123" -H "Content-Type: application/json" ^
  -d "{\"text\": \"Tell me about machine learning\", \"model\": \"llm\"}"

# 4. Upload an image (vision model)
curl -X POST http://localhost:8000/vision/analyze -H "X-API-Key: test-key-123" ^
  -F "file=@your_image.jpg"

# 5. List available models
curl http://localhost:8000/models -H "X-API-Key: test-key-123"
```

> **Windows users:** In PowerShell use `curl.exe` (real curl) or the `^` line‑continuation.  
> **macOS/Linux:** swap `^` for `\`. Or copy the commands directly as shown above in your Powershell or terminal.

---

## 🧱 The Mental Model

```
Request → Middleware → Router → Dependency → Service → Response
            (logging,     (path    (auth,         (model      (Pydantic
             CORS)          params)  rate‑limit)   inference)   serialization)
```

Every production AI/ML API follows this exact pipeline. Learn it here, recognise it everywhere.

---

## 🚀 After This Guide

Once you've worked through the **Learning Path** and read the **Concepts**, try:

1. **Replace the model** — swap the mock `model.py` for real OpenAI / Anthropic calls; the async streaming structure stays the same.
2. **Add a rate‑limiter dependency** — there's a commented example in `auth.py`.
3. **Build an "OpenAI‑style" endpoint** — `/v1/chat/completions` with response schema identical to OpenAI's spec. You're 20 lines away.
4. **Wrap a locally run model** — use `asyncio.to_thread` to keep inference from blocking the event loop.
5. **Add these conversations** — check the `docs/CONCEPTS.md` §6 for job interview questions.

---

## ✨ Repository Credits

This project is built on the following open‑source stack:

- [**FastAPI**](https://fastapi.tiangolo.com) — the web framework powering the guide
- [**Pydantic**](https://docs.pydantic.dev) — data validation and serialisation
- [**Uvicorn**](https://www.uvicorn.org) — the ASGI server running the app
- [**pytest**](https://docs.pytest.org) — the test framework

---

## 📊 Popularity & Contributions

If this guide helped you, a ⭐ **star** on the repo helps others find it.

Contributions are welcome! File an issue or a PR if you spot anything — from typo fixes to new sections.

---

*No GPU required. Mock models. Real production patterns.*