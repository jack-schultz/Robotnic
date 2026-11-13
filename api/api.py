from fastapi import FastAPI
import uvicorn
from api.stats import stats, read_stats_history

app = FastAPI()


@app.get("/stats")
def get_stats():
    with stats.lock:
        return {
            "guilds": stats.guilds,
            "users": stats.users,
            "creators": stats.creators,
            "channels": stats.channels,
            "connected_users": stats.connected_users,
        }

@app.get("/stats/history")
def get_stats_history(days: int | None = None, interval: int | None = None):
    return read_stats_history(days=days, interval=interval if interval and interval > 0 else None)


@app.get("/")
def health():
    return {"ok": True}


def run_web(port):
    uvicorn.run(app, host="0.0.0.0", port=port)
