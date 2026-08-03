# FastAPI Concepts — From Zero to Production AI APIs

This file is the **conceptual companion** to the codebase. It starts from the very beginning — *what FastAPI even is* — and works up to the advanced patterns used in production AI platforms.

> **How to use this:** Read this *before* or *while* doing the hands-on steps in [`LEARNING_PATH.md`](LEARNING_PATH.md). Every concept here maps to a real file in this project — the *"Where it lives"* boxes point you there.

---

## 1. What is FastAPI?

**FastAPI is a Python framework for building web APIs** — a way to turn Python functions into HTTP endpoints (URLs that other programs call).

Three facts that define it:

1. **It's modern (async-first).** Built on top of `Starlette` (the HTTP layer) and `Pydantic` (the data layer). Released 2018, quickly became the standard for AI/ML teams.
2. **It's driven by type hints.** You write plain Python with type annotations, and FastAPI does the heavy lifting for you.
3. **It gives you free documentation.** Every endpoint you write is automatically documented at `/docs` (Swagger UI) and `/redoc`.

```
┌─────────────────────────────────────────────────────────┐
│                     FastAPI (the glue)                  │
│                                                         │
│   ┌──────────────┐     ┌─────────────────────────────┐  │
│   │   Starlette  │     │          Pydantic           │  │
│   │  (handles    │     │   (handles data: validation │  │
│   │   HTTP,      │     │    serialization, settings) │  │
│   │   routing,   │     └─────────────────────────────┘  │
│   │   ASGI)      │                                      │
│   └──────────────┘                                      │
│                                                         │
│   + uvicorn = the actual server that runs it            │
└─────────────────────────────────────────────────────────┘
```

**The stack in one sentence:** `uvicorn` is the server that receives raw HTTP bytes → `Starlette` routes them to the right function → `Pydantic` validates the data in/out → your Python function runs → the result goes back out as HTTP.

**Where it lives:** `requirements.txt` (`fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`).

---

## 2. How Does FastAPI Work?

### The three pillars

FastAPI isn't magic — it's three ideas working together:

| Pillar | What it does | Example in this project |
|---|---|---|
| **Type hints** | Your function signature declares what the API accepts and returns | `async def predict(body: PredictRequest)` |
| **Pydantic** | Reads those hints → validates JSON → gives you typed objects | `schemas/request.py`, `schemas/response.py` |
| **OpenAPI schema** | Generates an interactive spec of your whole API, served at `/docs` | `http://localhost:8000/docs` |

Because you declare the *shape* of your data once (in the type hints), FastAPI derives everything else: validation, serialization, documentation, and even a client SDK if you want one.

### The request lifecycle

Every HTTP request flows through the same pipeline. Understand this and you understand FastAPI:

```
 Client
   │  1. HTTP request (POST /predict, JSON body, X-API-Key header)
   ▼
┌──────────────────────────────────────────────────────────────┐
│  uvicorn server — receives the raw HTTP bytes                │
│    │                                                          │
│    ▼                                                          │
│  Middleware 1 (LoggingMiddleware) — log, time, request ID     │
│    │                                                          │
│    ▼                                                          │
│  Middleware 2 (CORS) — browser-safety headers                 │
│    │                                                          │
│    ▼                                                          │
│  Router — matches URL → finds the right endpoint function     │
│    │                                                          │
│    ▼                                                          │
│  Dependencies — auth check runs first (verify_api_key)        │
│    │                                                          │
│    ▼                                                          │
│  Pydantic — validates the JSON body into PredictRequest       │
│    │                                                          │
│    ▼                                                          │
│  Your function — calls the model service                      │
│    │                                                          │
│    ▼                                                          │
│  Pydantic — serializes PredictResponse back to JSON           │
│    │                                                          │
│    ▼                                                          │
│  Background tasks — billing/logging run AFTER response        │
└──────────────────────────────────────────────────────────────┘
   │  2. HTTP response back to the client
   ▼
 Client
```

**Where it lives:** every file. This is the map — `main.py` wires the middlewares and routers, `middleware/` is the top two boxes, `routers/` is the route matching, `middleware/auth.py` is the dependency gate, `schemas/` is validation, `services/` is your function.

### ASGI vs WSGI (the old way)

- **WSGI** (Flask, Django's old default) is synchronous. One request = one thread. Slow I/O (waiting on a model, a database, an API call) *blocks* the thread.
- **ASGI** (FastAPI, Starlette) is asynchronous. A request that's waiting on I/O *yields* — the server handles other requests meanwhile.

For AI this matters enormously: **model inference is I/O bound** (you wait on a GPU, a model server, or an external LLM API). With ASGI, 100 concurrent inference calls can all be "in flight" while each one waits for its model call to return.

---

## 3. The Core Concepts (in the order you'll hit them)

### 3.1 Configuration with pydantic-settings

**The problem:** API keys, model paths, batch sizes, env flags — scattered `os.environ.get()` calls become a mess.

**The solution:** one `Settings` class. Pydantic reads `.env`, validates types, and exposes a typed object everywhere.

```python
class Settings(BaseSettings):
    api_key: str = "test-key-123"
    max_input_length: int = 2000   # must be an int — Pydantic enforces it
```

**Why AI engineers need it:** model paths, device (`"cuda"` vs `"cpu"`), API keys for OpenAI/Anthropic, and env-specific toggles all live here. A config typo fails *at startup*, not in production.

**Where it lives:** `app/config.py`.

### 3.2 Path & Query Parameters

Two ways to pass data in the URL:

```
Path parameter:  /models/{model_name}    →  model_name = "sentiment"   (required, part of URL)
Query parameter: /models?available_only=false  →  available_only = False (optional, after "?")
```

- FastAPI reads both **from the function signature** — no manual parsing.
- Path params are required. Query params are optional *if* they have a default.

```python
@router.get("/models/{model_name}")          # path param in URL braces
async def get_model(model_name: str): ...

@router.get("/models")                        # query param from function default
async def list_models(available_only: bool = Query(default=True)): ...
```

**Why AI engineers need it:** inference endpoints commonly use query params for filters (`top_k`, `max_tokens`), and path params for model IDs.

**Where it lives:** `app/routers/health.py` (path), `app/routers/predict.py` (query).

### 3.3 Request Bodies & Pydantic Validation

When the client sends JSON, you define its shape with a Pydantic model. FastAPI then:

1. Parses the JSON into a typed Python object
2. Validates every field (`min_length`, `ge`, `le`, `Literal`)
3. Returns **422** with a clear message if validation fails
4. Shows the schema in `/docs`

```python
class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    model: Literal["sentiment", "summarizer", "llm"] = "sentiment"
```

**The key insight:** you never write `if temperature < 0 or temperature > 2: raise ...`. The type hint IS the validation. Garbage never reaches your expensive model.

**Where it lives:** `app/schemas/request.py`. Try sending `{"text": "", "temperature": 5}` to `/predict` and watch the 422.

### 3.4 Response Models

The flip side: declare what the API *returns*, and FastAPI serializes it, filters unknown fields, and documents it.

```python
class PredictResponse(BaseModel):
    request_id: str
    output: str
    confidence: Optional[float] = None
```

Set `response_model=PredictResponse` on the route. Bonus: FastAPI validates the *output* too — a buggy service returning a bad shape is caught before it reaches the client. If a field isn't in the model, it's **dropped** (so you can't accidentally leak internal fields like DB IDs).

**Where it lives:** `app/schemas/response.py`, used in `app/routers/predict.py`.

### 3.5 Dependency Injection — the most important pattern

**The problem:** auth, DB sessions, model loading, rate limits — repeated at the top of every endpoint. Copy-pasting leads to bugs.

**The solution:** write the logic **once** as a function, then declare it in the route signature:

```python
async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    if x_api_key != settings.api_key:
        raise HTTPException(401, "Invalid API key")
    return x_api_key

@router.post("/predict")
async def predict(body: PredictRequest, _: str = Depends(verify_api_key)):
    ...
```

**Mental model:** `Depends(fn)` = "before calling this route, run `fn`. If it raises, the route never runs." Like a bouncer: invalid ID → nobody gets in.

**Why AI engineers need it:** dependencies are how production AI APIs do auth, rate limiting (`Depends(check_rate_limit)`), loading the model once (`Depends(get_model)`), and database sessions (`Depends(get_db)`). Dependencies can even depend on other dependencies (chain them).

**Where it lives:** `app/middleware/auth.py` (defined), `app/routers/predict.py`, `stream.py`, `vision.py` (injected).

### 3.6 Middleware

**The problem:** some things apply to *every* request — logging, timing, request IDs, CORS, rate limiting.

**The solution:** middleware sits *between* the client and your routes. Every request passes through it in, and every response passes back through it.

```
Client → [LoggingMiddleware] → [CORSMiddleware] → Route → ... → back out
```

It's a stack — the **last middleware added runs first**. `app.add_middleware(LoggingMiddleware)` then `app.add_middleware(CORSMiddleware)` means: request hits Logging first, then CORS, then the route.

**Why AI engineers need it:** track p95/p99 inference latency, attach `X-Request-ID` to every response so you can trace a request through logs, add auth/rate-limit headers globally.

**Where it lives:** `app/middleware/logging_mw.py` (defined), `app/main.py` (registered). Check the `X-Request-ID` header on any response.

### 3.7 Async/Await — when to use it

FastAPI is async, but **not everything should be async**. The rule of thumb for AI:

| Operation | Use |
|---|---|
| Calling OpenAI / Anthropic / a model server | `async def` + `await` |
| File / network I/O | `async def` + `await` |
| Running a LOCAL model (PyTorch forward pass) | `def`, or `await asyncio.to_thread(model, input)` |
| Pure CPU computation (numpy, pandas) | `def` |

```python
# WRONG — blocks the event loop, slows down ALL requests
async def predict(body):
    result = my_heavy_model(body.text)   # CPU work in async def = bad

# RIGHT — offload to a thread pool
async def predict(body):
    result = await asyncio.to_thread(my_heavy_model, body.text)
```

FastAPI runs plain `def` functions in a thread pool automatically, so you don't block anything. Reserve `async def` for *waiting* on I/O.

**Where it lives:** `app/services/model_service.py` — note `async def predict` (I/O bound in reality) and the `await asyncio.sleep(...)` simulations.

### 3.8 Streaming (SSE) — how ChatGPT-style output works

LLM latency is high. Instead of making users stare at a spinner, stream tokens as they're generated.

```
POST /stream → server keeps connection open
   ← data: The \n\n
   ← data: quick \n\n
   ← data: brown \n\n
   ← data: [DONE] \n\n
   (connection closes)
```

Mechanics:
- The endpoint returns a `StreamingResponse` wrapping an **async generator**.
- The async generator `yield`s one token at a time; FastAPI pushes each chunk immediately.
- `data: <content>\n\n` is **Server-Sent Events (SSE)**, a web standard consumed natively by browser `EventSource`.

```python
@app.post("/stream")
async def stream(body: StreamRequest):
    return StreamingResponse(
        token_generator(body.text, body.max_tokens),  # async generator
        media_type="text/event-stream",
    )
```

**Why AI engineers MUST know this:** OpenAI, Anthropic, Gemini all stream this way. You'll implement it for any LLM product. Test it live with `curl -N` (the `-N` disables curl's buffering so you see tokens arrive).

**Where it lives:** `app/routers/stream.py`, `app/services/model_service.py` (`stream_tokens`).

### 3.9 Background Tasks

Some work shouldn't make the client wait: billing counters, audit logs, metrics, sending notifications.

`BackgroundTasks` runs the function **after** the response is sent:

```python
background_tasks.add_task(log_inference, request_id=..., model=..., tokens=...)
```

Client gets their answer instantly; the logging happens in the background. **Where it lives:** `app/routers/predict.py` — watch the terminal: the response arrives, *then* the `[background] ...` log line appears.

### 3.10 Lifespan Events (startup / shutdown)

Loading an ML model takes 5–30 seconds. You want to load it **once at startup**, not on every request, and free GPU memory at shutdown.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = load_model()   # startup: before yield
    yield                             # app runs here
    app.state.model.unload()          # shutdown: after yield
```

This replaces the old `@app.on_event("startup")` (deprecated). The context-manager form guarantees cleanup runs even if startup fails.

**Where it lives:** `app/main.py` — watch the `🚀` / `🛑` prints when you start/stop uvicorn.

### 3.11 Exception Handling

Instead of try/except in every route, register **global** handlers:

```python
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(400, {"error": "Invalid input", "detail": str(exc)})

@app.exception_handler(Exception)   # last resort → 500
async def general_exception_handler(request, exc):
    return JSONResponse(500, {"error": "Internal server error", ...})
```

**Best practice:** an API must always return JSON errors (your clients are code, not humans). In production, hook the 500 handler to Sentry/Datadog. **Where it lives:** `app/main.py`.

### 3.12 Routers — organizing a growing API

Splitting routes into modules keeps each file focused as your platform grows (like OpenAI's `/v1/chat/completions`, `/v1/embeddings`, `/v1/images/generate`):

```
app/routers/
  predict.py   ← /predict, /models        (inference)
  stream.py    ← /stream                  (streaming)
  vision.py    ← /vision/analyze          (file uploads)
  health.py    ← /health, /models/{name}  (public, no auth)
```

Each router is an `APIRouter`. Different routers can have different prefixes, auth, or rate limits. They're assembled in `app/main.py` via `app.include_router(...)`.

### 3.13 File Uploads

Models take more than text — images (GPT-4V), audio (Whisper), PDFs (RAG). FastAPI uses `UploadFile` with `multipart/form-data`:

```python
@app.post("/vision/analyze")
async def analyze_image(file: UploadFile = File(...)):
    contents = await file.read()
```

Key differences from JSON endpoints: `Content-Type: multipart/form-data`, and you use `File(...)` instead of a body model. **Always validate content-type and size server-side** (415 / 413 errors) — never trust the client. **Where it lives:** `app/routers/vision.py`.

---

## 4. Why FastAPI Over Flask? (the classic comparison)

| | Flask | FastAPI |
|---|---|---|
| Async support | Needs extra setup (gevent/threads) | Built-in (`async def`) |
| Input validation | Manual | Automatic (Pydantic) |
| API docs | Manual (Swagger plugin) | Auto-generated at `/docs` |
| Type hints | Optional | Core to how it works |
| Performance | Slower (sync) | Faster (ASGI + uvicorn) |
| Data types | `dict` | Typed Pydantic models |

**The one insight that matters for AI:** model calls are I/O bound — you're waiting on a GPU, a model server, or an external API. FastAPI's async model handles hundreds of concurrent waiting requests; a sync Flask server blocks the whole process on one slow inference.

---

## 5. What AI Engineers Actually Build With FastAPI

### A. Wrapping an LLM API
```python
@app.post("/chat")
async def chat(body: ChatRequest):
    response = await openai.chat.completions.create(
        model="gpt-4", messages=body.messages, stream=True,
    )
    return StreamingResponse(stream_openai(response), media_type="text/event-stream")
```

### B. Serving a Local Model
```python
@app.post("/embed")
async def embed(body: EmbedRequest):
    embedding = await asyncio.to_thread(model.encode, body.text)  # don't block the loop
    return {"embedding": embedding.tolist()}
```

### C. RAG Pipeline Endpoint
```python
@app.post("/rag/query")
async def rag_query(body: QueryRequest, db=Depends(get_vector_db)):
    query_vec = await asyncio.to_thread(embed_model.encode, body.query)
    docs = await db.search(query_vec, top_k=5)
    answer = await llm.generate(context=docs, question=body.query)
    return {"answer": answer, "sources": docs}
```

**Notice:** the same patterns from Section 3 — dependencies for the DB, async for I/O, response models — repeated. This is why the project teaches them.

---

## 6. Common Interview Questions

**Q: What's the difference between a path parameter and a query parameter?**
- Path param: `/models/{name}` → part of the URL, always required.
- Query param: `/models?available=true` → after the `?`, optional with defaults.

**Q: How do you load an ML model efficiently in FastAPI?**
- Load it in the lifespan startup and store on `app.state`.
- OR instantiate it once at module level in the service file (simpler).
- NEVER load it inside the route function — it would reload on every request.

**Q: How would you add rate limiting to an inference endpoint?**
- A dependency that checks a counter (Redis-backed in prod) and raises `HTTPException(429)` past the limit. Attach with `Depends(rate_limit_check)`.

**Q: What HTTP status code should an inference endpoint return?**
- `200` success · `422` invalid input (Pydantic, automatic) · `401` missing/wrong API key · `429` rate limited · `503` model overloaded/not ready.

**Q: When is `async def` the wrong choice in FastAPI?**
- When your function does heavy CPU work (a local model forward pass). Use a plain `def` (thread pool) or `asyncio.to_thread`, or you'll block the event loop and slow down every other request.

---

## 7. Mental Model — Putting It All Together

```
Request → Middleware → Router → Dependency → Service → Response
          (logging,     (URL      (auth,       (model    (Pydantic
           CORS)         match)    rate limit)  inference) model)
```

Every production AI inference API — OpenAI, Anthropic, Hugging Face — is this exact pipeline, with more dependencies bolted on (DB sessions, vector stores, telemetry). Master this project's flow and you've learned the template for all of them.
