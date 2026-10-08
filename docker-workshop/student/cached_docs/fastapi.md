# FastAPI — Quickstart (cached fallback)

Create a file `main.py`:

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello World"}
```

Run the development server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The app object is named `app` and is imported by uvicorn as `main:app`.
Visiting `GET /` returns the JSON response `{"message": "Hello World"}`.

To add another route, decorate another function:

```python
@app.get("/health")
def health():
    return {"status": "ok"}
```
