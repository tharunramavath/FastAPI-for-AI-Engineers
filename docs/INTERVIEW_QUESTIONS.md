# 🎯 FastAPI for AI Engineers — Interview Questions & Answers

> A comprehensive question bank for AI / ML engineering interviews that involve FastAPI.
> Each question has a **direct answer** (what you say in the interview) plus a **code snippet** and a **detailed explanation** so you actually understand it, not just memorize it.
>
> Every answer is grounded in this repo — the same patterns OpenAI, Anthropic, and Hugging Face use in production.

---

## 📚 Table of Contents

1. [Core FastAPI Concepts](#a-core-fastapi-concepts)
2. [Async, Concurrency & Performance](#b-async-concurrency--performance)
3. [Streaming & Server-Sent Events](#c-streaming--server-sent-events)
4. [Auth & Security](#d-auth--security)
5. [Validation & Error Handling](#e-validation--error-handling)
6. [Testing](#f-testing)
7. [AI-Specific Questions (RAG, Vector DB, Model Serving)](#g-ai-specific-questions)
8. [System Design & Architecture](#h-system-design--architecture)
9. [Production & Deployment](#i-production--deployment)
10. [Behavioral / Situational](#j-behavioral--situational)
11. [Quick Fire — 1-Line Answers](#k-quick-fire--1-line-answers)

---

## A. Core FastAPI Concepts

### Q1. What is FastAPI, and how does it work?

**Direct answer:** FastAPI is a modern Python web framework for building APIs. It's built on top of **Starlette** (the ASGI web layer) and **Pydantic** (the data validation layer). It uses Python type hints to automatically handle request validation, serialization, and API documentation. Because it's ASGI-based and async-native, it's a great fit for serving AI models, where inference is I/O bound.

**Code snippet:**
```python
from fastapi import FastAPI

app = FastAPI(title="My Model API")

@app.get("/")
async def root():
    return {"message": "Hello, world"}
```

**Detailed explanation:**
- FastAPI sits on two pillars: **Starlette** handles routing, middleware, ASGI, and web sockets; **Pydantic** handles data parsing, validation, and serialization.
- You declare the *shape* of your data once with type hints. From that, FastAPI derives: request validation, response serialization, and an interactive OpenAPI spec served at `/docs`.
- The same type hints are used by your editor (autocomplete) and your tests (typed contracts).
- The request lifecycle: client → uvicorn → middleware → router → dependency → Pydantic validation → your function → Pydantic serialization → response.
- In this repo, `app/main.py` is the entry point you pass to uvicorn: `uvicorn app.main:app --reload`.

---

### Q2. What are Pydantic models, and why are they so important in FastAPI?

**Direct answer:** Pydantic models are Python classes that define the structure, types, and constraints of data. FastAPI uses them as the request body and response model contracts. They validate incoming data, coerce types, and generate JSON schemas automatically — so invalid input never reaches your model.

**Code snippet:**
```python
from pydantic import BaseModel, Field

class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    model: Literal["sentiment", "summarizer", "llm"] = "sentiment"
```

**Detailed explanation:**
- Pydantic does four things automatically: **parses** JSON into typed objects, **validates** constraints (`min_length`, `ge`, `le`, `Literal`), **returns 422** with clear messages when validation fails, and **generates** the schema shown in `/docs`.
- `Field(...)` means required; `Field(default=...)` makes it optional.
- `Literal[...]` restricts a field to an exact set of values — perfect for model names so someone can't send `model="gpt-99"`.
- Custom logic goes in `@field_validator`, e.g. stripping whitespace before the model sees it.
- **Why AI engineers need this:** LLM APIs need strict input validation (max tokens, temperature ranges). Garbage input is expensive — you don't want a malformed request hitting a GPU.
- See `app/schemas/request.py` in this repo.

---

### Q3. What's the difference between a path parameter and a query parameter?

**Direct answer:** A path parameter is a required part of the URL itself (`/models/{name}`), while a query parameter is an optional key-value pair after the `?` (`/models?available=true`). FastAPI captures both from the function signature automatically.

**Code snippet:**
```python
# Path parameter — part of the URL, required
@router.get("/models/{model_name}")
async def get_model(model_name: str):
    return {"name": model_name}

# Query parameter — after "?", optional with a default
@router.get("/models")
async def list_models(available_only: bool = Query(default=True)):
    return {"filtered": available_only}
```

**Detailed explanation:**
- Path params use braces in the route string and are always required. Missing one → 404.
- Query params come from the function's default values and are optional. Missing one → default used.
- Use `Path(...)` and `Query(...)` to add validation and documentation (`examples`, `ge`, `le`, etc.).
- `GET /models/sentiment` → `model_name = "sentiment"`. `GET /models?available_only=false` → `available_only = False`.
- See `app/routers/health.py` (path) and `app/routers/predict.py` (query).

---

### Q4. Explain dependency injection in FastAPI. Give a real AI example.

**Direct answer:** Dependency injection means writing shared logic (auth, DB sessions, model loading, rate limiting) **once** as a function and letting FastAPI call it automatically before a route runs. You declare the dependency in the route signature with `Depends()`, and FastAPI handles calling it, caching it per-request, and passing the result to your function.

**Code snippet:**
```python
async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@router.post("/predict")
async def predict(body: PredictRequest, _: str = Depends(verify_api_key)):
    ...
```

**Detailed explanation:**
- Without DI you'd copy-paste auth checks into every endpoint. With DI you write it once.
- If the dependency raises `HTTPException`, the route **never runs** — perfect for a "bouncer" pattern.
- Dependencies can depend on other dependencies (chaining): e.g. `rate_limited_auth(api_key=Depends(verify_api_key))`.
- Real AI uses:
  - Auth: `Depends(verify_api_key)`
  - Loading the model once: `Depends(get_model)`
  - Database / vector DB session: `Depends(get_db)`
  - Rate limiting: `Depends(check_rate_limit)`
- The `_: str = Depends(...)` underscore means "run it for side effects, I don't need the value."
- See `app/middleware/auth.py`.

---

### Q5. What are FastAPI routers, and why split endpoints across them?

**Direct answer:** An `APIRouter` is a group of related endpoints. You split endpoints into routers so each file focuses on one domain, and assemble them in `main.py` with `app.include_router(...)`. This keeps the codebase maintainable as the API grows.

**Code snippet:**
```python
# app/routers/predict.py
router = APIRouter(tags=["Inference"])

@router.post("/predict")
async def predict(...): ...

# app/main.py
from app.routers import predict, stream, vision, health
app.include_router(predict.router)
app.include_router(stream.router)
app.include_router(vision.router)
app.include_router(health.router)
```

**Detailed explanation:**
- As an AI platform grows you get many endpoint families: `/v1/chat/completions`, `/v1/embeddings`, `/v1/images/generate`, `/v1/audio/transcribe` (like OpenAI).
- Each router can have its **own prefix, tags, dependencies, and rate limits**.
- In this repo: `predict.py` (/predict), `stream.py` (/stream), `vision.py` (/vision/analyze), `health.py` (/health, /models/{name}).
- This is the same modular structure every production API uses.

---

### Q6. How does middleware work in FastAPI?

**Direct answer:** Middleware sits *between* the client and the route handlers. Every request passes through middleware before reaching the endpoint, and every response passes back through it. It's for cross-cutting concerns: logging, timing, request IDs, CORS, rate limiting.

**Code snippet:**
```python
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.time()
        response = await call_next(request)      # forward to the route
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{(time.time()-start)*1000:.1f}ms"
        return response
```

**Detailed explanation:**
- `call_next(request)` forwards the request down the stack to the next middleware or the route.
- Middleware is a **stack** — the LAST one added runs FIRST. So `app.add_middleware(LoggingMiddleware)` then `app.add_middleware(CORSMiddleware)` means Logging runs first on the way in.
- Why AI engineers need it: attach `X-Request-ID` to every response so you can trace one request through logs; measure p95/p99 inference latency; enforce global headers.
- See `app/middleware/logging_mw.py`.

---

### Q7. What is the lifespan pattern, and why use it for ML models?

**Direct answer:** Lifespan is the modern way to run code at startup and shutdown. Code before `yield` runs at startup (load the model, connect to DB), code after `yield` runs at shutdown (free GPU memory, flush logs). It replaces the deprecated `@app.on_event("startup")`.

**Code snippet:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = load_model()   # startup — happens ONCE
    yield                            # app is serving requests here
    app.state.model.unload()         # shutdown

app = FastAPI(lifespan=lifespan)
```

**Detailed explanation:**
- Loading an ML model takes 5–30 seconds. You must do it **once** at startup, never on every request.
- The context-manager form guarantees cleanup even if startup fails (like a `finally`).
- Alternative: load the model once at module level in a service file (`model_service = ModelService()`), which is what this repo does for simplicity.
- The old `@app.on_event` is deprecated — always use lifespan for new code.
- See `app/main.py` — you'll see the `🚀` / `🛑` prints on start/stop.

---

## B. Async, Concurrency & Performance

### Q8. When should a FastAPI route be `async def` vs `def`?

**Direct answer:** Use `async def` when the function waits on **I/O** (calling an external API, file reads, network calls). Use plain `def` for **CPU-bound** work (running a local model forward pass). FastAPI runs sync `def` functions in a thread pool automatically, so they don't block other requests.

**Code snippet:**
```python
# I/O bound → async
@router.post("/predict")
async def predict(body: PredictRequest):
    result = await model_service.predict(body.text)  # network / model server call

# CPU bound → def (FastAPI runs it in a thread pool)
@router.post("/embed")
def embed(body: EmbedRequest):
    return model.encode(body.text)  # local PyTorch forward pass
```

**Detailed explanation:**
- Rule of thumb for AI:
  | Operation | Use |
  |---|---|
  | Calling OpenAI / Anthropic | `async def` + `await` |
  | Calling a model server (Triton, TorchServe) | `async def` + `await` |
  | Reading/writing files | `async def` + `await` |
  | Running a LOCAL model (PyTorch forward pass) | `def` or `asyncio.to_thread` |
  | Pure computation (numpy, pandas) | `def` |
- `async def` is for *waiting*, not for *computing*. If you put CPU-heavy code inside an `async def` without `to_thread`, you **block the event loop** and slow down all requests.

---

### Q9. How do you run a CPU-heavy ML model without blocking the server?

**Direct answer:** Wrap the blocking call in `asyncio.to_thread(...)`. This offloads the synchronous model call to a worker thread so the event loop stays free to handle other requests.

**Code snippet:**
```python
@app.post("/embed")
async def embed(body: EmbedRequest):
    # model.encode is CPU-bound — don't block the loop
    embedding = await asyncio.to_thread(model.encode, body.text)
    return {"embedding": embedding.tolist()}
```

**Detailed explanation:**
- `asyncio.to_thread(func, *args)` runs `func` in a separate thread and returns an awaitable.
- The event loop keeps serving other requests while the model runs on the thread.
- The "WRONG" version: calling `model.encode(...)` directly inside an `async def` blocks everything for the duration of the forward pass.
- For very heavy GPU work, in production you'd typically use a model server (TorchServe/Triton) and call it over HTTP — which is naturally async.

---

### Q10. What's the difference between ASGI and WSGI?

**Direct answer:** WSGI is the old synchronous Python web-server interface (Flask, Django's old default). ASGI is the modern asynchronous interface (FastAPI, Starlette). ASGI supports async, WebSockets, and streaming, and it can handle many concurrent requests that are waiting on I/O without blocking.

**Code snippet:**
```
WSGI:  request → thread (blocked while waiting) → response
ASGI:  request → event loop (yield while waiting) → response
```

**Detailed explanation:**
- With WSGI, one slow model inference blocks that worker thread, and scaling means adding more threads/processes.
- With ASGI, a request waiting on a model call *yields* to the event loop; other requests proceed in the meantime.
- For AI this is critical: **inference is I/O bound**. You wait on a GPU, a model server, or an external LLM API. ASGI lets hundreds of those waits overlap.
- This is why FastAPI (ASGI + uvicorn) beats Flask (WSGI) for AI serving.

---

### Q11. How does FastAPI handle concurrency?

**Direct answer:** FastAPI is async-first and built on Starlette (ASGI). For I/O-bound work, it uses a single event loop with cooperative concurrency: many requests wait on I/O at once. For sync `def` routes, it uses a thread pool. So you get concurrency both ways.

**Detailed explanation:**
- `async def` routes run on the event loop — concurrency comes from `await` points.
- `def` routes run in a **thread pool** (anyio's default), so even legacy sync code doesn't serialize requests.
- For CPU/GPU-bound model work, use `asyncio.to_thread` or a separate model server.
- In this repo, `model_service.predict` uses `await asyncio.sleep(...)` to simulate a slow model call — try firing several `/predict` requests at once and watch them complete in parallel.

---

### Q12. What happens if you run a blocking call inside an `async def` route?

**Direct answer:** The event loop is blocked, and **every other request** in the process stalls until the blocking call finishes. That's the worst performance bug in async Python.

**Code snippet:**
```python
# BAD — blocks the event loop for ALL users
@app.post("/predict")
async def predict(body: PredictRequest):
    result = my_heavy_model(body.text)   # CPU bound, no await → blocks
    return result

# GOOD — offload to a thread
@app.post("/predict")
async def predict(body: PredictRequest):
    result = await asyncio.to_thread(my_heavy_model, body.text)
    return result
```

**Detailed explanation:**
- An `async def` that never hits an `await` runs its CPU work synchronously *on the event loop*. Nothing else can run until it returns.
- Since a single uvicorn worker has one event loop, one blocking call = the whole server goes unresponsive.
- Always offload CPU/GPU work with `asyncio.to_thread`, or call a model server over async HTTP.

---

## C. Streaming & Server-Sent Events

### Q13. How do you implement LLM token streaming in FastAPI?

**Direct answer:** Return a `StreamingResponse` that wraps an **async generator**. The generator `yield`s one token at a time, and FastAPI pushes each chunk to the client immediately. This is how ChatGPT-style output works.

**Code snippet:**
```python
async def token_generator(text: str, max_tokens: int):
    async for token in model_service.stream_tokens(text, max_tokens):
        if token == "[DONE]":
            yield "data: [DONE]\n\n"
        else:
            yield f"data: {token}\n\n"

@app.post("/stream")
async def stream_predict(body: StreamRequest, _=Depends(verify_api_key)):
    return StreamingResponse(
        content=token_generator(body.text, body.max_tokens),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

**Detailed explanation:**
- The `data: ...\n\n` format is **Server-Sent Events (SSE)**, a web standard. Each event ends with two newlines.
- The connection stays open; the server pushes chunks as they're produced instead of sending everything at the end.
- The `Cache-Control: no-cache` and `X-Accel-Buffering: no` headers stop proxies/browsers from buffering the stream.
- Test with `curl -N` (no-buffer) so you see tokens arrive live.
- See `app/routers/stream.py`.

---

### Q14. What is Server-Sent Events (SSE)? How is it different from WebSockets?

**Direct answer:** SSE is a one-way push protocol over plain HTTP where the server streams events (`data: ...\n\n`) to the client over a long-lived connection. WebSockets are a full-duplex (two-way) protocol. For LLM token streaming, SSE is the right tool: the client just receives tokens; it rarely needs to send data mid-stream.

**Code snippet:**
```
SSE wire format:
data: The \n\n
data: quick \n\n
data: brown \n\n
data: [DONE] \n\n
```

**Detailed explanation:**
- SSE is simpler: works over HTTP(S), auto-reconnects with `EventSource`, no special server support needed (any ASGI server works).
- WebSockets are bidirectional and lower-level — you need a WS server and more client complexity.
- OpenAI, Anthropic, and Gemini all use SSE-style streaming for chat completions.
- Browser side: `new EventSource("/stream")`; on `onmessage` you append `event.data`.

---

### Q15. How would you integrate OpenAI streaming with a FastAPI endpoint?

**Direct answer:** Make the OpenAI call with `stream=True`, iterate the response chunks in an async generator, and forward each chunk through a `StreamingResponse`.

**Code snippet:**
```python
@app.post("/chat")
async def chat(body: ChatRequest):
    async def generate():
        stream = await openai.chat.completions.create(
            model="gpt-4", messages=body.messages, stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield f"data: {chunk.choices[0].delta.content}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

**Detailed explanation:**
- The async generator structure is identical to this repo's `token_generator` — the only difference is the source of tokens (OpenAI vs a mock).
- Because both the upstream call and the downstream response are async, the whole pipeline is non-blocking.
- Always forward a `[DONE]` sentinel (OpenAI uses the same convention) so clients know the stream ended.

---

## D. Auth & Security

### Q16. How do you authenticate API requests in FastAPI?

**Direct answer:** Write a dependency that validates a credential (API key header, OAuth2 token, JWT) and attach it to protected routes with `Depends(...)`. If the credential is invalid, raise `HTTPException` — the route never runs.

**Code snippet:**
```python
async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return x_api_key

# Usage on any protected route:
@router.post("/predict")
async def predict(body: PredictRequest, _: str = Depends(verify_api_key)):
    ...
```

**Detailed explanation:**
- `Header(..., alias="X-API-Key")` reads the HTTP header; `alias` maps the hyphenated header name to the Python variable name.
- Keep the dependency **reusable**: attach it to any route with one line.
- The `WWW-Authenticate` header is standard HTTP practice — it tells clients which scheme is expected.
- For JWT/OAuth2, the dependency would decode the token instead of comparing a static key.
- Public endpoints (health checks) simply omit the dependency.
- See `app/middleware/auth.py`.

---

### Q17. How do you add rate limiting to an AI inference endpoint?

**Direct answer:** Create a dependency that counts requests per API key and raises `HTTPException(429)` when the limit is exceeded. Use a fast store (Redis in production) for the counter.

**Code snippet:**
```python
async def rate_limited_auth(api_key: str = Depends(verify_api_key)):
    count = await redis.incr(f"rate:{api_key}")   # atomic increment
    if count == 1:
        await redis.expire(f"rate:{api_key}", 60)  # 1-minute window
    if count > 100:
        raise HTTPException(429, "Rate limit exceeded")
    return api_key

# Then protect the expensive endpoint:
@router.post("/predict")
async def predict(body: PredictRequest, _: str = Depends(rate_limited_auth)):
    ...
```

**Detailed explanation:**
- Dependencies can chain: `rate_limited_auth` depends on `verify_api_key`, so auth runs first, then the rate check.
- `INCR` + `EXPIRE` in Redis is the standard "sliding window" implementation and is atomic — no race conditions.
- 429 = Too Many Requests, the correct status code for rate limiting.
- For this repo, a simple in-memory dict keyed by API key would work for learning; Redis is what you'd use in production.

---

### Q18. Why should health checks stay public (no auth)?

**Direct answer:** Load balancers and Kubernetes probes call `/health` — they don't have API keys. If the health endpoint required auth, infrastructure couldn't verify whether your pod is ready to serve traffic.

**Detailed explanation:**
- Kubernetes liveness/readiness probes hit `/health` directly; they can't send your API key.
- The health endpoint must be **fast** (<50ms) and **public**, so orchestrators can route traffic only to healthy instances.
- Protected endpoints (inference, billing) still require auth.
- See `app/routers/health.py` — note it has no `Depends(verify_api_key)`.

---

### Q19. How do you keep secrets (API keys, model paths) out of the code?

**Direct answer:** Use environment variables via `pydantic-settings`. A `Settings` class reads `.env` (or the environment) with type hints, and you import one singleton everywhere. The `.env` file is git-ignored; only `.env.example` is committed.

**Code snippet:**
```python
class Settings(BaseSettings):
    api_key: str = "test-key-123"
    model_path: str = "/models/llm-7b"
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
```

**Detailed explanation:**
- Pydantic validates config at **startup** — a typo (`MAX_INPUT_LENGTH=abc`) fails fast instead of crashing at request time.
- Never hardcode keys; never commit `.env`. The `.gitignore` in this repo excludes it.
- In production you'd inject secrets from a secrets manager or CI/CD environment variables.
- See `app/config.py`.

---

## E. Validation & Error Handling

### Q20. What's the difference between 400 and 422 in FastAPI?

**Direct answer:** `422 Unprocessable Entity` is what Pydantic returns for **validation failures** — the request is well-formed JSON but a field violates its constraints (missing field, wrong type, out of range). `400 Bad Request` is for **semantic errors** — the request is structurally valid but logically wrong (e.g. empty text after stripping).

**Code snippet:**
```python
# 422 — Pydantic's automatic response for a bad body:
# {"text": "", "temperature": 5.0}  → 422 (min_length, le)

# 400 — you raise it for semantic rules:
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(status_code=400, content={"error": "Invalid input", "detail": str(exc)})
```

**Detailed explanation:**
- 422 comes from Pydantic automatically; the response includes a structured list of which field failed and why.
- 400 is reserved for errors *you* define (custom validation, business rules).
- This repo maps `ValueError` → 400 via a global exception handler.
- 401 = bad/absent credentials, 404 = not found, 413 = file too large, 415 = unsupported media type, 429 = rate limited, 500 = unexpected server error, 503 = model overloaded/not ready.

---

### Q21. How do you define global exception handlers in FastAPI?

**Direct answer:** Register `@app.exception_handler(...)` functions. They catch exceptions raised anywhere in the app and return a consistent JSON error instead of an HTML error page.

**Code snippet:**
```python
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"error": "Invalid input", "detail": str(exc)})

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # In production: log to Sentry / Datadog here
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
```

**Detailed explanation:**
- Without this, an unhandled exception returns an HTML traceback — useless for API clients.
- The `Exception` handler is the "last resort" for anything uncaught. Hook it up to Sentry/Datadog in production.
- Handlers are registered centrally in `app/main.py`, so routes stay clean of try/except noise.
- An API must **always** return JSON errors; your clients are code, not humans.

---

### Q22. What is a response model, and why use one?

**Direct answer:** A response model is a Pydantic class that declares the *output* shape. FastAPI serializes your return value to match it, filters out fields you don't want to expose, validates the output, and documents it in `/docs`.

**Code snippet:**
```python
class PredictResponse(BaseModel):
    request_id: str
    output: str
    confidence: Optional[float] = None
    latency_ms: float

@router.post("/predict", response_model=PredictResponse)
async def predict(...):
    ...
    return result   # FastAPI validates + serializes to PredictResponse
```

**Detailed explanation:**
- If the service returns an object with extra fields (like an internal DB ID), the response model **drops** them — you can't accidentally leak internals.
- If the service returns a malformed shape, FastAPI catches it before it hits the client.
- Consistent output shape across all endpoints is what clients (and OpenAI-style SDKs) rely on.
- See `app/schemas/response.py`.

---

### Q23. How do you validate file uploads (content type, size)?

**Direct answer:** Use `UploadFile` with `File(...)`, then check `content_type` and the byte length server-side. Return `415` for unsupported types and `413` for oversized files.

**Code snippet:**
```python
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@app.post("/vision/analyze", response_model=VisionResponse)
async def analyze_image(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, detail=f"Unsupported type: {file.content_type}")
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(413, detail="File too large")
    ...
```

**Detailed explanation:**
- Multipart form uploads use `Content-Type: multipart/form-data` — different from JSON bodies. That's why `python-multipart` is a dependency.
- `UploadFile` gives `.filename`, `.content_type`, `await file.read()`, `await file.seek(0)`.
- **Never trust the client**: always validate MIME type and size on the server.
- This is the pattern for vision models (GPT-4V), audio (Whisper), and RAG document uploads.
- See `app/routers/vision.py`.

---

## F. Testing

### Q24. How do you test FastAPI endpoints?

**Direct answer:** Use `fastapi.testclient.TestClient` (wraps httpx) with pytest. It simulates HTTP requests against the app in memory — no live server needed. Write tests for happy paths, auth failures, validation failures, 404s, and response schemas.

**Code snippet:**
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
HEADERS = {"X-API-Key": "test-key-123"}

def test_predict_with_valid_key_succeeds():
    r = client.post("/predict", json={"text": "I love this!", "model": "sentiment"}, headers=HEADERS)
    assert r.status_code == 200
    assert "output" in r.json()

def test_predict_with_wrong_key_returns_401():
    r = client.post("/predict", json={"text": "hi"}, headers={"X-API-Key": "wrong"})
    assert r.status_code == 401
```

**Detailed explanation:**
- `TestClient` uses the ASGI transport directly — tests run in milliseconds.
- Run with `pytest tests/ -v`. This repo has 13 passing tests (`tests/test_predict.py`).
- Tests are your **executable documentation**: they pin down what the API *must* do, so CI catches regressions before deploy.

---

### Q25. How do you test streaming endpoints?

**Direct answer:** Use `TestClient` with `stream=True` on the request, then iterate the response lines and assert you received SSE events.

**Code snippet:**
```python
def test_stream_returns_sse_tokens():
    with client.stream("POST", "/stream", json={"text": "hi", "max_tokens": 5}, headers=HEADERS) as r:
        assert r.status_code == 200
        assert r.headers["content-type"] == "text/event-stream"
        body = "".join(r.iter_text())
    assert "data:" in body
    assert "data: [DONE]" in body
```

**Detailed explanation:**
- `client.stream(...)` keeps the connection open so you can read chunks as they arrive.
- Assert the `text/event-stream` content type and that the body ends with `[DONE]`.
- Background tasks and streaming add latency to tests — keep mock delays tiny (this repo uses 50ms).

---

## G. AI-Specific Questions

### Q26. How do you serve a locally loaded ML model with FastAPI?

**Direct answer:** Load the model **once** (lifespan or module-level singleton), then call it through `asyncio.to_thread` so the forward pass doesn't block the event loop.

**Code snippet:**
```python
# app/services/model_service.py — instantiated once, imported everywhere
model_service = ModelService()

# route
@app.post("/embed")
async def embed(body: EmbedRequest):
    embedding = await asyncio.to_thread(model_service.encode, body.text)
    return {"embedding": embedding.tolist()}
```

**Detailed explanation:**
- NEVER load the model inside the route function — it would reload on every request (10–30s each!).
- Options ranked: (1) lifespan + `app.state.model`, (2) module-level singleton service, (3) external model server.
- For GPU-bound models, `to_thread` protects the event loop but the GPU is still the bottleneck — scale workers/GPUs, or move the model behind TorchServe/Triton.
- See `app/services/model_service.py` — it's mocked with realistic delays to teach the pattern.

---

### Q27. How would you build a RAG query endpoint in FastAPI?

**Direct answer:** Combine three async stages: embed the query, search the vector DB, then generate an answer with the retrieved context. Dependencies inject the embed model and vector DB.

**Code snippet:**
```python
@app.post("/rag/query")
async def rag_query(body: QueryRequest, db=Depends(get_vector_db)):
    query_vec = await asyncio.to_thread(embed_model.encode, body.query)
    docs = await db.search(query_vec, top_k=5)          # vector DB async client
    answer = await llm.generate(context=docs, question=body.query)
    return {"answer": answer, "sources": [d.id for d in docs]}
```

**Detailed explanation:**
- The embed step is CPU-bound → `asyncio.to_thread`.
- The vector DB search is I/O → `await` an async client (Chroma, Pinecone, Qdrant, pgvector).
- The generation step is I/O → `await` the LLM call; can be streamed with the SSE pattern from Q13.
- FastAPI's dependency injection makes swapping the vector DB trivial: change one dependency function.

---

### Q28. How do you handle a model that is slow or not ready?

**Direct answer:** Separate health checks (`/health` = alive, `/ready` = model loaded) and return `503 Service Unavailable` from a dependency when the model isn't ready. Give slow models async + streaming so users see partial output instead of a long spinner.

**Code snippet:**
```python
def get_model():
    if not app.state.model_loaded:
        raise HTTPException(503, "Model not ready")
    return app.state.model

@app.get("/ready")
async def ready():
    return {"ready": app.state.model_loaded}

@app.post("/predict")
async def predict(body: PredictRequest, model=Depends(get_model)):
    ...
```

**Detailed explanation:**
- 503 tells orchestrators and clients "try later", not "you sent a bad request".
- Kubernetes readiness probes can use `/ready` to stop routing traffic to a pod whose model is still loading.
- For slow-but-usable models, streaming (SSE) makes the product feel responsive even when time-to-first-token is seconds.

---

## H. System Design & Architecture

### Q29. Walk me through the full request lifecycle of an inference endpoint.

**Direct answer:** Client → uvicorn → middleware → router → dependency (auth) → Pydantic validation → route handler → model service → Pydantic serialization → response → (background task). Every production AI API is this pipeline.

**Code snippet:**
```
Request → Middleware → Router → Dependency → Service → Response
           (logging,     (URL     (auth,       (model    (Pydantic
            CORS)         match)   rate limit)  inference) serialization)
```

**Detailed explanation:**
- **Middleware** (logging, request ID, CORS) wraps everything.
- **Router** matches the URL to the right handler.
- **Dependencies** (auth, rate limit, DB/model injection) run before the handler; if any raises, the handler never runs.
- **Pydantic** validates the body into a typed model.
- **Service layer** does the actual inference (async).
- **Pydantic** serializes the response; **background tasks** (billing/metrics/logging) run after the client gets their answer.
- This is exactly what OpenAI's API does, at much bigger scale. See `docs/CONCEPTS.md` §2 and `app/main.py`.

---

### Q30. How do you scale a FastAPI AI service? Where do the bottlenecks live?

**Direct answer:** Scale by process (uvicorn workers / multiple replicas) plus scale out the *real* bottlenecks — GPU/model serving, vector DB, and LLM API calls — which are typically separate services.

**Code snippet:**
```bash
# Multiple uvicorn workers on one machine
uvicorn app.main:app --workers 4

# But for GPU-heavy inference, prefer:
#   a model server (TorchServe/Triton) behind the API
#   + async I/O so the API never waits idly on inference
```

**Detailed explanation:**
- The API layer is rarely the bottleneck — **model inference and external calls** are.
- Bottleneck hierarchy: GPU/model server > vector DB > LLM API latency > API process.
- Patterns: separate the model behind a model server; use a queue (Redis/ Celery) for long-running batch jobs; stream instead of blocking; load-test with a realistic concurrent mix.
- The async design of FastAPI (this repo's pattern) ensures the API process can hold hundreds of in-flight requests while each waits on I/O.

---

### Q31. How do you design a multi-model AI platform (like OpenAI's)?

**Direct answer:** Use routers per model family, a registry of model metadata, a common request/response schema, and versioned prefixes (`/v1`). Auth, rate limits, and telemetry live in shared dependencies/middleware.

**Code snippet:**
```python
# Model registry — metadata only, cheap to keep in memory
AVAILABLE_MODELS = {
    "sentiment": ModelInfo(name="sentiment", input_type="text", max_tokens=50, is_available=True),
    "llm": ModelInfo(name="llm", input_type="text", max_tokens=2048, is_available=True),
}

@router.get("/models")
async def list_models(available_only: bool = Query(True), _=Depends(verify_api_key)):
    models = AVAILABLE_MODELS.values()
    if available_only:
        models = [m for m in models if m.is_available]
    return ModelsResponse(models=list(models), total=len(models))
```

**Detailed explanation:**
- Routers = `/v1/chat/completions`, `/v1/embeddings`, `/v1/images/generate`, `/v1/audio/transcribe`.
- A metadata registry (`ModelInfo`) powers `/models`, `/models/{name}`, and health checks without loading every model.
- Shared schemas keep every endpoint's request/response shape consistent (Q22).
- Shared dependencies apply auth/rate limits uniformly (Q4, Q17).
- See `app/services/model_service.py` and `app/routers/predict.py`.

---

### Q32. What is the service-layer pattern, and why does it matter for AI?

**Direct answer:** The service layer isolates *business logic* (model loading, inference, processing) from *HTTP concerns* (params, headers, status codes). Routers handle HTTP; services handle AI. You can swap the mock for real OpenAI/local models without touching routes.

**Code snippet:**
```python
# Router — HTTP only
@router.post("/predict", response_model=PredictResponse)
async def predict(body: PredictRequest, _=Depends(verify_api_key)):
    return await model_service.predict(text=body.text, model_name=body.model)

# Service — the model logic (swappable)
class ModelService:
    async def predict(self, text, model_name, ...) -> PredictResponse:
        ...
```

**Detailed explanation:**
- Separation of concerns: a router test doesn't need a GPU; a service test doesn't need an HTTP client.
- Swapping mock → OpenAI → local GPU model is a change in the service layer only.
- This is the same layering used in every serious AI platform.
- See `app/routers/predict.py` and `app/services/model_service.py`.

---

## I. Production & Deployment

### Q33. What is CORS, and when do you need it in FastAPI?

**Direct answer:** CORS (Cross-Origin Resource Sharing) lets a browser app on one origin (e.g. `http://localhost:3000`) call your API on another (`http://localhost:8000`). Browsers enforce same-origin by default, so you configure allowed origins on the API.

**Code snippet:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],                          # dev only — wide open
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Production: allow_origins=["https://your-frontend.com"]
```

**Detailed explanation:**
- Without CORS, a browser frontend calling `/predict` gets a blocked-request error even though the API works fine in curl.
- `allow_origins=["*"]` is fine for dev but a security risk in production — restrict to your actual frontend domain(s).
- CORS is a **browser** mechanism; non-browser clients (curl, server-to-server) ignore it entirely.

---

### Q34. How do you add observability (logging, metrics, tracing) to a FastAPI AI API?

**Direct answer:** Middleware for request logging + `X-Request-ID` for tracing, structured logs (JSON), metrics counters for latency/model usage, and optional OpenTelemetry for distributed tracing. Hook the global 500 handler to an error tracker (Sentry/Datadog).

**Code snippet:**
```python
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.time()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{(time.time()-start)*1000:.1f}ms"
        logger.info({"request_id": request_id, "status": response.status_code, ...})
        return response
```

**Detailed explanation:**
- `X-Request-ID` ties every log line and trace for one request together — this is how you debug a single user's bad inference call.
- Track p95/p99 latency: inference APIs live and die by their latency tail.
- In production, ship structured logs to CloudWatch/Datadog and errors to Sentry.
- See `app/middleware/logging_mw.py`.

---

### Q35. How do you handle graceful shutdown (free GPU memory, flush logs)?

**Direct answer:** Put cleanup in the lifespan `yield` (shutdown section). When the server stops, the model unloads, GPU memory frees, and logs flush — guaranteed even on errors.

**Code snippet:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = load_model()      # startup
    yield
    app.state.model.unload()            # shutdown — free GPU memory
    await flush_logs()
```

**Detailed explanation:**
- The context manager guarantees shutdown code runs (like a `finally`), even if startup partially failed.
- Uvicorn sends SIGINT/SIGTERM → lifespan shutdown runs → workers drain in-flight requests before exiting.
- Never rely on `atexit` or OS teardown for GPU memory — explicit cleanup prevents OOM on the next run.
- See `app/main.py` (`🛑 Shutting down...`).

---

## J. Behavioral / Situational

### Q36. "You just joined a startup. They have a trained sentiment model in a notebook and want it behind an API in a week. What do you do?"

**Suggested answer (structure):**
1. **Inspect the model** — framework (PyTorch/transformers), size, GPU requirements, expected latency.
2. **Wrap it in a service layer** — the exact `ModelService` pattern in this repo: load once, async predict.
3. **Define the API contract** — Pydantic request/response schemas (text in, structured JSON out).
4. **Add auth + rate limiting** as shared dependencies.
5. **Stream if latency is high** — SSE streaming so the UX feels fast.
6. **Test it** — `TestClient` + pytest; pin down status codes and schemas.
7. **Deploy** — uvicorn workers behind a load balancer, `/health` for probes, metrics/logs in place.
8. **Iterate** — swap mock for real inference, add batching if needed.

---

### Q37. "An LLM endpoint is timing out in production. How do you debug it?"

**Suggested answer (structure):**
1. **Check logs for the `X-Request-ID`** — trace one failing request end-to-end.
2. **Identify where time is spent** — client connect? auth? queue? model? upstream LLM call? (metrics at each stage).
3. **Timeouts** — upstream LLM providers time out under load; add retries with backoff and a per-stage timeout.
4. **Streaming** — if users are hitting the timeout waiting for the *full* response, switch to SSE streaming so tokens arrive early.
5. **Scaling** — model server concurrency, worker count, queue depth.
6. **Load test** — reproduce with a realistic concurrent mix; watch p95/p99.
7. **Fail fast** — reject requests early (429/503) instead of letting them pile up and time out.

---

### Q38. "How would you expose an OpenAI-style chat endpoint that supports both streaming and non-streaming?"

**Suggested answer (structure):**
- Use a Pydantic `ChatCompletionRequest` with a `stream: bool` field.
- `stream=False`: call the LLM once, return the full JSON completion (`{"choices": [{"message": {...}}]}`).
- `stream=True`: return `StreamingResponse` with SSE events, ending with `data: [DONE]`.
- Same request/response shape as OpenAI so existing clients work.
- Add auth, rate limits, and usage tracking via dependencies; log tokens used per request for billing.

---

## K. Quick Fire — 1-Line Answers

**Q: What is a 422?** — Pydantic validation failure (wrong type, missing field, out of range).
**Q: What is a 401?** — Missing or invalid credentials. **429?** — Rate limited. **503?** — Not ready/overloaded.
**Q: How do you load a model once?** — Lifespan startup or module-level singleton.
**Q: When not to use `async def`?** — For CPU-bound local model inference; use `def` or `asyncio.to_thread`.
**Q: What is `Depends()`?** — DI: FastAPI calls the function before the route and injects its return value.
**Q: Path vs query param?** — `/models/{name}` vs `/models?filter=x`.
**Q: What powers FastAPI?** — Starlette (HTTP/ASGI) + Pydantic (validation/serialization).
**Q: What is the SSE wire format?** — `data: <payload>\n\n`.
**Q: Why stream LLM output?** — LLM latency is high; streaming makes UX feel responsive (ChatGPT does this).
**Q: How do you test an endpoint without a server?** — `TestClient(app)` from `fastapi.testclient`.
**Q: Where do cross-cutting concerns live?** — Middleware (logging, CORS) and dependencies (auth, rate limits).
**Q: Why use response models?** — Consistent output shape; drops internal fields; validated + documented.
**Q: What is the lifespan pattern?** — Startup/shutdown lifecycle via `@asynccontextmanager`; replaced `on_event`.
**Q: Why is FastAPI good for AI?** — Async (I/O-bound inference), typed validation, auto docs, streaming built in.

---

*Study the [Learning Path](LEARNING_PATH.md) hands-on, read the [Core Concepts](CONCEPTS.md) for the "why", and practice these answers out loud. Good luck! 🚀*