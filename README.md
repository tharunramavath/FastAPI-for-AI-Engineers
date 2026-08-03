# 🤖 FastAPI for AI Engineers — One Project, Everything You Need

> Learn FastAPI the way AI engineers actually use it: building a production-style **AI Model Serving API**.

> 🌐 **Live interactive guide:** <https://tharunramavath.github.io/FastAPI-for-AI-Engineers/> — cream/red themed site with sidebar navigation.

> ⭐ **New to this repo? Start here:** [`docs/LEARNING_PATH.md`](docs/LEARNING_PATH.md) — a step-by-step hands-on guide with *what to read, what to run, what to observe, and what to learn* at every step.

---

## 🎯 What You'll Build

A REST API that:
- Accepts text and runs it through an ML model (mocked, so no GPU needed)
- Streams responses back (like ChatGPT does)
- Handles authentication, rate limiting, and error handling
- Serves model metadata and health checks
- Follows patterns used at real AI companies (OpenAI, Hugging Face, Anthropic-style APIs)

---

## 🗺️ Learning Map — Concepts Covered

| Concept | Where It's Taught | Why AI Engineers Need It |
|---|---|---|
| Path & Query Parameters | `routers/predict.py` | Every inference endpoint uses these |
| Request Body (Pydantic) | `schemas/` | Validating model inputs |
| Response Models | `schemas/` | Structuring model outputs |
| Async/Await | `services/model_service.py` | Model inference is I/O bound |
| Streaming Responses | `routers/stream.py` | LLM token streaming |
| Background Tasks | `routers/predict.py` | Logging, metrics after inference |
| Dependency Injection | `routers/`, `middleware/auth.py` | Auth, DB, model loading |
| Middleware | `middleware/` | Logging, rate limiting |
| Exception Handling | `app/main.py` | Graceful error responses |
| Lifespan Events | `app/main.py` | Loading ML models at startup |
| File Uploads | `routers/vision.py` | Image/audio model inputs |
| Router Organization | `routers/` | Structuring multi-model APIs |
| Environment Config | `config.py` | API keys, model paths |
| OpenAPI Docs | Auto-generated | Sharing your API with teammates |

---

## 📁 Project Structure

```
ai-fastapi-project/
├── app/
│   ├── main.py              ← App entry point, lifespan, exception handlers
│   ├── config.py            ← Settings with pydantic-settings
│   ├── routers/
│   │   ├── predict.py       ← Core inference endpoint (text → prediction)
│   │   ├── stream.py        ← Streaming endpoint (SSE / token streaming)
│   │   ├── vision.py        ← File upload endpoint (image input)
│   │   └── health.py        ← Health check & model metadata
│   ├── schemas/
│   │   ├── request.py       ← Input validation (Pydantic models)
│   │   └── response.py      ← Output structures
│   ├── services/
│   │   └── model_service.py ← Business logic, model calls (mocked)
│   └── middleware/
│       ├── auth.py          ← API key authentication
│       └── logging_mw.py    ← Request/response logging
├── tests/
│   └── test_predict.py      ← How to test FastAPI apps
├── docs/
│   └── CONCEPTS.md          ← Deep-dive explanations of each concept
├── requirements.txt
├── .env.example
└── README.md                ← You are here
```

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up environment
```bash
cp .env.example .env
# Edit .env — set your API_KEY to anything, e.g. "test-key-123"
```

### 3. Run the server
```bash
uvicorn app.main:app --reload
```

### 4. Open the interactive docs
```
http://localhost:8000/docs        ← Swagger UI (click "Try it out"!)
http://localhost:8000/redoc       ← ReDoc (cleaner reading)
```

---

## 🧪 Try These Requests (in order)

```bash
# 1. Health check — no auth needed
curl http://localhost:8000/health

# 2. Predict — requires API key in header
curl -X POST http://localhost:8000/predict \
  -H "X-API-Key: test-key-123" \
  -H "Content-Type: application/json" \
  -d '{"text": "I love this product", "model": "sentiment", "max_tokens": 100}'

# 3. Stream tokens — watch them arrive one by one
curl -N http://localhost:8000/stream \
  -H "X-API-Key: test-key-123" \
  -H "Content-Type: application/json" \
  -d '{"text": "Tell me about machine learning", "model": "llm"}'

# 4. Upload an image (vision model)
curl -X POST http://localhost:8000/vision/analyze \
  -H "X-API-Key: test-key-123" \
  -F "file=@any_image.jpg"

# 5. List available models
curl http://localhost:8000/models \
  -H "X-API-Key: test-key-123"
```

---

## 📚 Reading Order (if you want to learn, not just run)

For the full guided walkthrough with commands, observations, and exercises, follow **[`docs/LEARNING_PATH.md`](docs/LEARNING_PATH.md)** (13 steps, ~1–2 hours).

Reading order (if you want to learn, not just run):
1. **`app/config.py`** — Understand settings first (2 min)
2. **`app/schemas/request.py`** + **`response.py`** — Pydantic models (10 min)
3. **`app/main.py`** — App structure, lifespan, exception handlers (10 min)
4. **`app/middleware/auth.py`** — Dependency injection pattern (5 min)
5. **`app/routers/predict.py`** — Core endpoint patterns (15 min)
6. **`app/routers/stream.py`** — Streaming (10 min)
7. **`app/routers/vision.py`** — File uploads (5 min)
8. **`app/services/model_service.py`** — Where your actual model code lives (10 min)
9. **`tests/test_predict.py`** — Testing (10 min)
10. **`docs/CONCEPTS.md`** — Deep dives on anything confusing

---

## 🔑 Key Mental Model

```
Request → Middleware → Router → Dependency → Service → Response
           (auth,        (path,    (inject       (your      (Pydantic
            logging)      params)   model)        ML code)   model)
```

Every AI inference API in the industry follows this exact pattern.
