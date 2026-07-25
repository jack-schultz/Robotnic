from fastapi import FastAPI
import uvicorn
from api.stats import stats

app = FastAPI()


@app.get("/stats")
def get_stats():
    with stats.lock:
        return {
            "guilds": stats.guilds,
            "users": stats.users,
            "creators": stats.creators,
            "channels": stats.channels,
        }

@app.get("/")
def health():
    return {"ok": True}


def run_web(port):
    uvicorn.run(app, host="0.0.0.0", port=port)
