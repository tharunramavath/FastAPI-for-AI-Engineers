# 🗺️ Hands-On Learning Path — Build an AI Model Serving API with FastAPI

> **Read → Run → Observe → Learn.** Every step in this guide follows that loop.
> You will NOT learn by reading alone. You must run the commands and look at the output.

---

## 📋 How to Use This Guide

Each **Step** is a self-contained lesson with the same four sections:

| Section | What it tells you |
|---|---|
| **📖 Read** | The file(s) to open. Read the comments in the file too — they teach the concept. |
| **▶️ Run** | The exact command to execute. The server must be running for most of these. |
| **👀 Observe** | What to look at in the output. This is the "aha" moment. |
| **🎓 Learn** | The concept you just internalized + the question you should be able to answer. |

### Rules of the road

1. **One server, many steps.** Start the server once (Step 1) and leave it running while you do Steps 2–11. Each step only restarts it if needed.
2. **Restart the server after Step 3** so you see the startup/shutdown logs. The `--reload` flag means FastAPI auto-restarts when you save a file — you'll see this happen.
3. **Use `/docs` at every step.** Open `http://localhost:8000/docs` and click **"Try it out"** — it's the fastest way to poke an endpoint without curl.
4. **Windows PowerShell tip:** use `curl.exe` (not `curl`). In PowerShell 5.1, `curl` is an alias for `Invoke-WebRequest` and ignores `-H`/`-d`. `curl.exe` is the real curl and is bundled with Windows 10+.
5. **When stuck:** `python -m pytest tests -q` should always pass at the end of every step. If it fails, you changed something you shouldn't have.

---

## 🚦 Phase 0 — Environment & First Run

### Step 0 — Setup

**📖 Read** (skim only, don't dwell):
- `requirements.txt` — the exact dependency list. Note `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `python-multipart`, `httpx`, `pytest`.
- `.env.example` and `.env` — your environment variables. `API_KEY=test-key-123` is what you'll use in every curl command.

**▶️ Run** (from the project root):

```bash
# 1. Create and activate the virtual environment (one time)
python -m venv .venv

# Windows PowerShell
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy the env template (Windows PowerShell: Copy-Item)
cp .env.example .env
```

**▶️ Run** (verify your Python environment is ready):

```bash
# All of these should work without error:
python -c "import fastapi; print(fastapi.__version__)"
python -c "import uvicorn; print('uvicorn ok')"
```

**👀 Observe:** Version numbers print without errors. If you see `ModuleNotFoundError`, you skipped install or activated the wrong venv.

**🎓 Learn:** A virtual environment isolates your dependencies so project A can have FastAPI 0.111 and project B can have 1.x. This is non-negotiable in real AI projects — conflicts between package versions (torch, transformers, fastapi) will destroy your day.

---

### Step 1 — Run the Server

**📖 Read:** `app/main.py` — just the top section (the docstring, lines 1–32). You'll read the whole file properly in Step 3.

**▶️ Run:**

```bash
uvicorn app.main:app --reload
```

**👀 Observe:**
- Terminal shows `Uvicorn running on http://127.0.0.1:8000`.
- You see the startup prints: `🚀 Starting AI Model Serving API...`, `✅ Startup complete — ready to serve requests`.
- Now visit `http://localhost:8000/docs` — Swagger UI appears with every endpoint documented **for free**.

**▶️ Run** (in a second terminal):

```bash
curl.exe http://localhost:8000/health
curl.exe http://localhost:8000/health | python -m json.tool
```

**👀 Observe:**
- Raw JSON on the first call, pretty-printed on the second.
- Fields: `status`, `environment`, `models_loaded`, `uptime_seconds`.

**🎓 Learn:**
- `uvicorn app.main:app` means: import module `app.main`, grab the object named `app` (your FastAPI instance), and serve it.
- `--reload` watches your files and restarts the server when you save. **Watch the terminal the first time you save a file later — you'll see it reload.**
- FastAPI generates the `/docs` (Swagger) and `/redoc` (ReDoc) UIs automatically from your type hints. No extra code. This alone is a reason AI teams use FastAPI.

---

## 🏗️ Phase 1 — Understand the Skeleton

### Step 2 — Configuration (`app/config.py`)

**📖 Read:** `app/config.py` — all of it.

**▶️ Run:**

```bash
# Change the value in .env and watch the API react (no code change needed):
curl.exe http://localhost:8000/health
```

1. Edit `.env`, set `ENVIRONMENT=staging`, save.
2. Wait ~2 seconds for `--reload` to pick up changes (actually .env changes need a manual restart — the server reloads on *Python file* changes, not .env).
3. Stop the server (Ctrl+C), run `uvicorn app.main:app --reload` again.
4. Call `/health` again.

**👀 Observe:** `"environment"` changed from `"development"` to `"staging"`. One config value, reflected everywhere, with zero code changes.

**▶️ Run** (now test the type-safety):

```bash
# Set MAX_INPUT_LENGTH=abc in .env, then restart uvicorn:
uvicorn app.main:app --reload
```

**👀 Observe:** The server **refuses to start** with a `validation error for Settings... MAX_INPUT_LENGTH: Input should be a valid integer`. Pydantic caught a bad config value at startup instead of failing mysteriously at request time.

**🎓 Learn:**
- `BaseSettings` from `pydantic-settings` reads `.env`, OS environment variables, and type-hints your config. Field `api_key` maps to env var `API_KEY`.
- **Config values are validated at startup.** A typo in a config type fails fast, not deep in your code.
- The `settings = Settings()` singleton is imported everywhere. One source of truth for `API_KEY`, `APP_NAME`, etc.

---

### Step 3 — Pydantic Schemas (`app/schemas/request.py` & `response.py`)

**📖 Read:** `app/schemas/request.py` and `app/schemas/response.py` — all of both.

**▶️ Run:** In `/docs`, expand **POST /predict**, click **Try it out**, and submit with the default example body.

**👀 Observe:**
- In the **Request Body** box, FastAPI shows a JSON *schema* — generated from the Python class. Try typing garbage in a field.
- Send `{"text": ""}` (empty text) → you get a **422** error with a message like `String should have at least 1 character`.
- Send `{"text": "hi", "temperature": 5}` → **422**, `Input should be less than or equal to 2.0`.
- Send `{"text": "hi", "model": "gpt-99"}` → **422**, only the `Literal` values are allowed.
- Now look at the **Response Body** of a successful call — it matches `PredictResponse` exactly: `request_id`, `model`, `output`, `confidence`, `tokens_used`, `latency_ms`, `timestamp`.

**▶️ Run** (confirm with curl):

```bash
curl.exe -X POST http://localhost:8000/predict ^
  -H "X-API-Key: test-key-123" ^
  -H "Content-Type: application/json" ^
  -d "{\"text\": \"\", \"model\": \"sentiment\"}"
```

**👀 Observe:** A 422 response. **You wrote zero validation code** — Pydantic did it all from the class definition.

**🎓 Learn:**
- **Request models** (Pydantic) = contract for *input*. `Field(..., min_length=1)` means required; `ge`/`le` set numeric bounds; `Literal` restricts to an exact set.
- **Response models** = contract for *output*. FastAPI serializes your Python object to match, and *drops* any field not in the model (e.g., you can't accidentally leak internal fields).
- Validation errors are `422 Unprocessable Entity` by design — the request was well-formed but semantically invalid. Clients can't fix malformed-JSON style errors; but they CAN fix 422s by reading the message.
- `@field_validator` lets you run custom logic (like `strip()` here) after the built-in checks.

---

### Step 4 — The App Wiring (`app/main.py`)

**📖 Read:** `app/main.py` — now read the **whole** file, including all the comments.

**▶️ Run:**
1. Watch the terminal while you **save** any Python file (e.g., add a blank line to `config.py` and save).
2. Press **Ctrl+C** in the uvicorn terminal.

**👀 Observe:**
- On save: uvicorn prints `Detected file change in ... Reloading...` then re-runs startup logs. **You never manually restarted.**
- On Ctrl+C: you see `🛑 Shutting down...` and `👋 Shutdown complete`. Startup and shutdown code ran around the lifetime of the app.

**▶️ Run** (test the exception handlers):

```bash
curl.exe http://localhost:8000/not-a-real-route
```

**👀 Observe:** A JSON `{"detail":"Not Found"}` — not an HTML 404 page. Every error from this API is JSON, because the clients are code.

**🎓 Learn:**
- **`lifespan`** is the modern replacement for `@app.on_event("startup")`. Code before `yield` runs at startup (load models, connect to DB), code after runs at shutdown (flush logs, free GPU).
- **Middleware is a stack.** `app.add_middleware(LoggingMiddleware)` then `CORSMiddleware` — the LAST added runs FIRST. Your LoggingMiddleware wraps CORS.
- **Global exception handlers** catch errors centrally instead of try/except everywhere. `ValueError` → 400, anything else → 500.
- `app.include_router(...)` assembles the app from smaller modules. `prefix=` would add a path prefix to all routes in a router.

---

## 🔐 Phase 2 — Cross-Cutting Concerns (Auth & Logging)

### Step 5 — Authentication Dependency (`app/middleware/auth.py`)

**📖 Read:** `app/middleware/auth.py` — all of it.

**▶️ Run:**

```bash
# No key at all:
curl.exe -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d "{\"text\": \"hi\"}"

# Wrong key:
curl.exe -X POST http://localhost:8000/predict -H "X-API-Key: wrong" -H "Content-Type: application/json" -d "{\"text\": \"hi\"}"

# Correct key:
curl.exe -X POST http://localhost:8000/predict -H "X-API-Key: test-key-123" -H "Content-Type: application/json" -d "{\"text\": \"hi\"}"
```

**👀 Observe:**
- No key → **422** (missing required `X-API-Key` *header* — it's a required param, so Pydantic rejects the request).
- Wrong key → **401** with your custom message from `auth.py`.
- Correct key → **200** with a prediction.

**▶️ Run** (prove the pattern is reusable):

```bash
curl.exe http://localhost:8000/models
curl.exe http://localhost:8000/health
```

**👀 Observe:** `/models` (protected by `Depends(verify_api_key)`) returns 422 without a key, but `/health` (no dependency) works with no key at all.

**🎓 Learn:**
- **Dependency Injection (`Depends`)**: write auth once in `verify_api_key`, then add `_: str = Depends(verify_api_key)` to any route to protect it. The underscore `_` means "run this for its side effects, I don't need the value."
- A dependency that raises `HTTPException` **short-circuits** the request — the route never runs. That's why auth code lives in one place, not pasted into every endpoint.
- `Header(..., alias="X-API-Key")` maps an HTTP header (hyphenated) to a Python argument (underscored). FastAPI reads it for you.
- **Health endpoints stay public on purpose** — Kubernetes/load balancers call `/health` and have no API key.

---

### Step 6 — Logging Middleware (`app/middleware/logging_mw.py`)

**📖 Read:** `app/middleware/logging_mw.py` — all of it.

**▶️ Run:**

```bash
curl.exe -X POST http://localhost:8000/predict -H "X-API-Key: test-key-123" -H "Content-Type: application/json" -d "{\"text\": \"hello there\"}"
```

**👀 Observe** the uvicorn terminal — you'll see lines like:

```
INFO:     127.0.0.1:55021 - "POST /predict HTTP/1.1" 200 OK
INFO | [a1b2c3d4] → POST /predict | client: 127.0.0.1
INFO | [a1b2c3d4] ← 200 | 15.3ms
INFO | [bg-log] [background] request_id=... model=sentiment tokens=...
```

**▶️ Run** (look at the response headers):

```bash
curl.exe -i http://localhost:8000/health
```

**👀 Observe:** Response includes `X-Request-ID: a1b2c3d4` and `X-Response-Time: 3.1ms`. The same `request_id` appears in both log lines — **that's how you trace one request through logs in production.**

**🎓 Learn:**
- **Middleware runs around every request**, both directions: before your route (`call_next`) and after it returns.
- Cross-cutting concerns (logging, timing, request IDs, CORS, rate limiting) belong in middleware so they apply to **every** endpoint automatically.
- The `X-Request-ID` pattern is how real platforms (Datadog, Sentry, New Relic) correlate logs for a single request.
- Note the background-task log line at the end — that's the `/predict` endpoint's `BackgroundTasks`, which we cover in Step 8.

---

## 🧠 Phase 3 — The Model Layer

### Step 7 — The Service Layer (`app/services/model_service.py`)

**📖 Read:** `app/services/model_service.py` — all of it.

**▶️ Run:**

```bash
# Slow down, watch the timing:
curl.exe -X POST http://localhost:8000/predict -H "X-API-Key: test-key-123" -H "Content-Type: application/json" -d "{\"text\": \"this is a test\", \"model\": \"sentiment\"}"
```

**👀 Observe:** `latency_ms` in the response is random (100–400ms simulated). The `confidence` field exists only for `sentiment`. Run the same call with `"model": "llm"` — `confidence` is now `null`.

**▶️ Run** (the streaming generator — watch it in real time):

```bash
curl.exe -N -X POST http://localhost:8000/stream -H "X-API-Key: test-key-123" -H "Content-Type: application/json" -d "{\"text\": \"explain deep learning\", \"max_tokens\": 20}"
```

**👀 Observe:** Tokens arrive **one at a time**, every 50ms, instead of the whole response at once. Words appear progressively, ending with `data: [DONE]`. This is exactly what ChatGPT feels like.

**🎓 Learn:**
- **Layering:** routers handle HTTP concerns (params, status codes); services handle business logic (inference). Swap `model_service` for a real OpenAI call and nothing in the routers changes.
- **`async def` vs `def`:** use `async` when your code waits on I/O (calling OpenAI, a GPU server, the filesystem) — the event loop serves other requests meanwhile. For heavy CPU work (a local model forward pass), use `await asyncio.to_thread(...)` or a plain `def` (FastAPI runs sync defs in a thread pool).
- **Async generators + `yield`** power streaming: `yield` one token, `await asyncio.sleep(0.05)`, yield the next. The function *remembers where it was* between yields.
- The module-level `model_service = ModelService()` is instantiated once — a simple version of "load the model once, reuse forever."

---

## 🔌 Phase 4 — The Endpoints (Routers)

### Step 8 — Health & Path Parameters (`app/routers/health.py`)

**📖 Read:** `app/routers/health.py` — all of it.

**▶️ Run:**

```bash
curl.exe http://localhost:8000/health
curl.exe http://localhost:8000/models/sentiment
curl.exe http://localhost:8000/models/gpt-99
```

**👀 Observe:**
- `/health` → the same JSON from Step 1, but now you know *why*: public endpoint, load balancers call it.
- `/models/sentiment` → metadata for one model, `{model_name}` captured from the URL.
- `/models/gpt-99` → **404** with a JSON message listing valid models.

**▶️ Run** (test the docs UI): in `/docs`, open **GET /models/{model_name}**, Try it out — note the "Examples" dropdown pre-fills `sentiment`, `summarizer`, `llm` (from `Path(examples=[...])`).

**🎓 Learn:**
- **Path parameters** (`/models/{model_name}`) are *required* parts of the URL. FastAPI maps them to function args automatically.
- `Path(...)` adds validation + documentation to path params.
- The `@router.get(...)` decorator means routers aren't just for POST — you group all model-related routes together regardless of HTTP method.

---

### Step 9 — The Core Endpoint (`app/routers/predict.py`)

**📖 Read:** `app/routers/predict.py` — the whole file. This is the most important file in the project.

**▶️ Run:**

```bash
curl.exe -X POST http://localhost:8000/predict -H "X-API-Key: test-key-123" -H "Content-Type: application/json" -d "{\"text\": \"The service was excellent and I highly recommend it\", \"model\": \"sentiment\"}"

curl.exe http://localhost:8000/models?available_only=false
curl.exe http://localhost:8000/models?available_only=true
```

**👀 Observe:**
- First call: full `PredictResponse` JSON with `request_id`, `latency_ms`, `confidence`.
- The two `/models` calls differ — `available_only=false` returns the same list here (all models are available), but the **query parameter** `?available_only=false` reached the function and changed the filter logic.

**▶️ Run** (see the background task fire):

```bash
# Watch the uvicorn terminal as you run this:
curl.exe -X POST http://localhost:8000/predict -H "X-API-Key: test-key-123" -H "Content-Type: application/json" -d "{\"text\": \"background test\", \"model\": \"summarizer\"}"
```

**👀 Observe:** The response comes back instantly, and **then** a `[background] request_id=... model=... tokens=...` line appears in the logs.

**🎓 Learn:**
- The complete request lifecycle: **Client → LoggingMiddleware → auth dependency → route → model_service → response → BackgroundTask**. You've now seen every link in the chain.
- **Query parameters** (`?available_only=false`) are optional, have defaults, and are read from the function signature. Path params = part of the URL; query params = options after `?`.
- **`BackgroundTasks`** let you return the response to the client first, then run slow bookkeeping (billing, metrics, audit logs, model logging) afterward. The client never waits for it.
- `response_model=PredictResponse` validates the *output* too — if the service returned a bad shape, FastAPI would catch it.
- This pattern — `POST` body + auth + service call + response model — is the template for **every** inference endpoint you'll ever write.

---

### Step 10 — Streaming (`app/routers/stream.py`)

**📖 Read:** `app/routers/stream.py` — all of it.

**▶️ Run:**

```bash
curl.exe -N -X POST http://localhost:8000/stream -H "X-API-Key: test-key-123" -H "Content-Type: application/json" -d "{\"text\": \"tell me about transformers\", \"max_tokens\": 30}"
```

**👀 Observe:** A stream of `data: ...\n\n` events, each holding one token, arriving every ~50ms, ending with `data: [DONE]\n\n`. Note the **Content-Type**: `text/event-stream`.

**▶️ Run** (compare to non-streaming):

```bash
# Without -N, curl buffers — you only see the end. With -N you see it live.
curl.exe -X POST http://localhost:8000/stream -H "X-API-Key: test-key-123" -H "Content-Type: application/json" -d "{\"text\": \"hi\"}"
```

**🎓 Learn:**
- **`StreamingResponse`** wraps an async generator and pushes each yielded chunk to the client as it's produced. The connection stays open until the generator finishes.
- The `data: ...\n\n` format is **Server-Sent Events (SSE)** — a web standard. JavaScript `EventSource` consumes it natively.
- Two newlines terminate each event; `data: [DONE]` signals the end (OpenAI uses the same convention).
- **`-N`/`--no-buffer`** in curl is how you *see* the streaming — without it curl hides the incremental arrival. That's why users see tokens appear live in ChatGPT-style UIs.

---

### Step 11 — File Uploads (`app/routers/vision.py`)

**📖 Read:** `app/routers/vision.py` — all of it.

**▶️ Run** (create a tiny test image, then upload it):

```bash
# Create a 1x1 red PNG (works on Windows PowerShell):
$bytes = [Convert]::FromBase64String("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
[IO.File]::WriteAllBytes("$PWD\test.png", $bytes)

curl.exe -X POST http://localhost:8000/vision/analyze ^
  -H "X-API-Key: test-key-123" ^
  -F "file=@test.png"

# Try uploading a text file instead — watch the rejection:
Set-Content -Path test.txt -Value "hello"
curl.exe -X POST http://localhost:8000/vision/analyze -H "X-API-Key: test-key-123" -F "file=@test.txt"
```

**👀 Observe:**
- PNG upload → `VisionResponse` with `filename`, `file_size_bytes`, random `detected_objects`, and `caption`.
- Text upload → **415 Unsupported Media Type**, a JSON error. Your server-side `ALLOWED_TYPES` check rejected it — never trust the client.

**🎓 Learn:**
- `UploadFile` handles multipart uploads: `.filename`, `.content_type`, `await file.read()`, `await file.seek(0)`.
- Requests with files use `Content-Type: multipart/form-data` (the `-F` flag), **not** `application/json`. That's why `python-multipart` is in requirements.
- **Always validate content-type AND size server-side.** Clients can send anything. 415 = unsupported media type, 413 = too large.
- This is the pattern for vision (GPT-4V), audio (Whisper), and RAG document uploads.

---

## ✅ Phase 5 — Testing

### Step 12 — Test Suite (`tests/test_predict.py`)

**📖 Read:** `tests/test_predict.py` — all of it.

**▶️ Run:**

```bash
python -m pytest tests -v
```

**👀 Observe:**
- 13 tests run, all pass. Each test function maps to a real behavior you just exercised manually: auth (401/422), validation (422), response shape, model listing, 404s.
- Look at `TestAuth::test_predict_without_key_returns_401` — the test *asserts* the exact contract you watched in Step 5.

**▶️ Run** (break a test on purpose):

1. In `.env`, change `API_KEY=test-key-123` to `API_KEY=other-key`.
2. Run `python -m pytest tests -v`.

**👀 Observe:** `test_predict_with_valid_key_succeeds` fails with a 401. **That's the point of tests** — they'd catch a rotated API key or a broken auth rule before you ship. Change the key back.

**🎓 Learn:**
- **`TestClient`** wraps the app with an in-memory HTTP client — no real server needed. Tests run in milliseconds.
- Tests are your **executable documentation**: they encode what the API *must* do (status codes, response shapes, edge cases).
- Write tests for: happy paths, auth failures, validation failures, 404s, response schema. Your CI pipeline runs these before every deploy.

---

## 🏁 Phase 6 — Solidify & Go Further

### Step 13 — Deep Dives & Mental Model

**📖 Read:** `docs/CONCEPTS.md` — read it *after* you've completed Steps 1–12. It re-explains everything you've seen from a higher level (when to use async, interview questions, real OpenAI/Anthropic patterns).

Preparing for an interview? Browse **[`docs/INTERVIEW_QUESTIONS.md`](INTERVIEW_QUESTIONS.md)** — a large question bank with direct answers, code snippets, and detailed explanations covering every concept in this project.

**▶️ Run:**

```bash
# Final self-check — everything green?
python -m pytest tests -q
```

**👀 Observe:** `13 passed`. You have now touched every file in this project.

**🎓 Learn — the key mental model:**

```
Request → Middleware → Router → Dependency → Service → Response
           (logging)    (path,    (auth)      (model
                        params)               inference)
```

Every production AI inference API (OpenAI, Anthropic, Hugging Face) is this exact pipeline with a few more dependencies (rate limiting, DB sessions, vector stores) bolted on.

### 💪 Challenges (do at least 2)

1. **Add a model** — add `"embedding"` to `AVAILABLE_MODELS` in `model_service.py` and to the `Literal` in `schemas/request.py`. Give it a mock output in `_mock_output`. Restart and call `/predict` with `"model": "embedding"`.
2. **Add a route** — create `routers/batch.py` with a `POST /batch/predict` that loops over a list of texts and calls `model_service.predict` for each. Register it in `main.py`. Test it in `/docs`.
3. **Rate limiting** — write a dependency in `auth.py` (there's a commented example) that counts calls per API key and raises `HTTPException(429)` after N. Attach it to `/predict`.
4. **Write a test** — add a test that uploads a fake image to `/vision/analyze` using `client.post` with `files={"file": ("x.png", b"...", "image/png")}`.
5. **Add CORS hardening** — change `allow_origins=["*"]` in `main.py` to your actual frontend origin and observe that a request from another origin is now blocked (check the `Access-Control-Allow-Origin` header).

### 📚 If you're going further

- **Real inference:** replace `_mock_output` with a call to the OpenAI / Anthropic API (`httpx.AsyncClient` is already a dependency). Keep the async structure — it's identical.
- **OpenAI-style API:** make a `/v1/chat/completions` route that returns `{"choices": [{"message": {...}}]}`. You're 20 lines from a ChatGPT clone.
- **Read:** `app/main.py` exception handlers + `docs/CONCEPTS.md` §9 (interview questions) before your next AI-platform interview.

---

## 🧾 Cheat Sheet — Every File in One Line

| File | One-liner |
|---|---|
| `app/main.py` | Glue: creates the app, lifespan, middleware, exception handlers, includes routers |
| `app/config.py` | Typed settings from `.env` via pydantic-settings |
| `app/schemas/request.py` | Pydantic *input* contracts (validation) |
| `app/schemas/response.py` | Pydantic *output* contracts (serialization) |
| `app/routers/health.py` | Public `/health` + path-param demo `/models/{name}` |
| `app/routers/predict.py` | The core POST /predict pattern + query params + background tasks |
| `app/routers/stream.py` | SSE token streaming |
| `app/routers/vision.py` | File uploads + content-type/size validation |
| `app/services/model_service.py` | The mock model layer (async inference + streaming) |
| `app/middleware/auth.py` | API-key auth as a reusable dependency |
| `app/middleware/logging_mw.py` | Request/response logging + X-Request-ID |
| `tests/test_predict.py` | 13 tests that pin down every behavior you learned |
| `docs/CONCEPTS.md` | "Why" behind each pattern + interview questions |
