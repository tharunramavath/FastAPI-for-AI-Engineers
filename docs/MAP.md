# 🗂️ Project Map

A quick orientation to every file in the repo. Read this to *see the whole system at a glance* — then use the [Learning Path](LEARNING_PATH.md) for the guided walkthrough and [Core Concepts](CONCEPTS.md) for the "why".

---

## Directory structure & one-line purpose

```
ai-fastapi-project/
├── app/
│   ├── main.py              ← entry point: app, lifespan, middleware, exception handlers
│   ├── config.py            ← typed settings from .env (pydantic-settings)
│   ├── routers/
│   │   ├── predict.py       ← POST /predict, GET /models (query params + background tasks)
│   │   ├── stream.py        ← POST /stream  (SSE token streaming)
│   │   ├── vision.py        ← POST /vision/analyze  (file uploads)
│   │   └── health.py        ← GET /health, GET /models/{name}  (path params, public)
│   ├── schemas/
│   │   ├── request.py       ← Pydantic *input* contracts (validation)
│   │   └── response.py      ← Pydantic *output* contracts (serialization)
│   ├── services/
│   │   └── model_service.py ← the model layer (mocked, async + streaming)
│   └── middleware/
│       ├── auth.py          ← API-key auth as a reusable dependency
│       └── logging_mw.py    ← request/response logging + X-Request-ID
├── tests/
│   └── test_predict.py      ← 13 tests (TestClient + pytest)
├── docs/                    ← this site + LEARNING_PATH.md + CONCEPTS.md
├── requirements.txt
├── .env.example             ← template (real .env is git-ignored)
└── README.md
```

## Request lifecycle → where each stage lives

```
Request → Middleware → Router → Dependency → Service → Response
           logging_mw   routers   verify_api_key   model_service   response.py
           + CORS        match     (auth)          (inference)     serializes out
```

## Cheat sheet — every file in one line

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
| `app/middleware/logging_mw.py` | Request/response logging + `X-Request-ID` |
| `tests/test_predict.py` | 13 tests that pin down every behavior you learned |
| `docs/CONCEPTS.md` | "Why" behind each pattern + interview questions |

## Key mental model

```
Request → Middleware → Router → Dependency → Service → Response
```

Every production AI inference API (OpenAI, Anthropic, Hugging Face) is this pipeline with a few more dependencies bolted on. Learn it here, recognize it everywhere.