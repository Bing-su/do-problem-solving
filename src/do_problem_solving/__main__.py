from __future__ import annotations

import atexit
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import diskcache as dc
import httpx

solved = "https://solved.ac/api/v3"
nfty = "https://ntfy.sh"
data_dir = Path(__file__).parent.joinpath("data")
cache = dc.Cache(data_dir)
atexit.register(cache.close)
ko_kr = ZoneInfo("Asia/Seoul")


@dataclass
class NotiInfo:
    handle: str
    topic: str
    url: str = nfty


def str_to_datetime(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")


def datetime_to_str(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def is_today(dt: datetime) -> bool:
    today = datetime.now(ko_kr).replace(hour=6, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    return today <= dt < tomorrow


def get_solved_count(handle: str) -> int:
    params = {"handle": handle}
    headers = {"Accept": "application/json", "User-Agent": "do-problem-solving"}
    resp = httpx.get(f"{solved}/users/show", params=params, headers=headers)
    resp.raise_for_status()

    # https://solvedac.github.io/unofficial-documentation/#/operations/getUser
    data = resp.json()
    if "solvedCount" not in data:
        msg = "`solvedCount` not found"
        raise RuntimeError(msg)

    return data["solvedCount"]


def update(handle: str, count: int) -> None:
    now = datetime.now(ko_kr)
    cache[handle] = {"time": datetime_to_str(now), "count": count}


def notify(info: NotiInfo) -> None:
    title = "Problem Solving"
    message = "문제풀어!"
    payload = {
        "title": title,
        "message": message,
    }
    resp = httpx.post(info.url, json=payload, follow_redirects=True)
    resp.raise_for_status()


def loop(info: NotiInfo) -> None:
    handle = info.handle
    current_count = get_solved_count(handle)
    if handle not in cache:
        notify(info)
        return

    cache_data = cache[handle]
    last_time_str = cache_data["time"]
    last_time = str_to_datetime(last_time_str)

    if not is_today(last_time):
        notify(info)
        update(handle, current_count)
        return

    if current_count > cache_data["count"]:
        update(handle, current_count)
        return

    notify(info)
