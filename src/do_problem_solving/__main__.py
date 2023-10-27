from __future__ import annotations

import re
import time
from dataclasses import dataclass

import click
import httpx
import schedule

solved = "https://solved.ac/api/v3"
nfty = "https://ntfy.sh/"
last_solved: int | None = None


@dataclass
class NotiInfo:
    handle: str
    topic: str
    url: str = nfty


def get_solved_count(handle: str) -> int:
    params = {"handle": handle}
    headers = {"Accept": "application/json", "User-Agent": "do-problem-solving"}
    resp = httpx.get(f"{solved}/user/show", params=params, headers=headers)
    resp.raise_for_status()

    # https://solvedac.github.io/unofficial-documentation/#/operations/getUser
    data = resp.json()
    if "solvedCount" not in data:
        msg = "`solvedCount` not found"
        raise RuntimeError(msg)

    return data["solvedCount"]


def notify(info: NotiInfo) -> None:
    base_url = httpx.URL(info.url)
    url = base_url.join(info.topic)
    title = "Problem Solving"
    message = "문제풀어!"
    headers = {"Title": title}
    resp = httpx.post(url, data=message, headers=headers, follow_redirects=True)
    resp.raise_for_status()


def loop(info: NotiInfo) -> None:
    global last_solved

    handle = info.handle
    current_solved = get_solved_count(handle)
    if last_solved is None or last_solved >= current_solved:
        notify(info)
        last_solved = current_solved


def on_six(info: NotiInfo) -> None:
    global last_solved

    last_solved = get_solved_count(info.handle)


def main(info: NotiInfo, times: list[str]) -> None:
    schedule.every().day.at("06:00:10", tz="Asia/Seoul").do(on_six, info)
    for t in times:
        schedule.every().day.at(t, tz="Asia/Seoul").do(loop, info)

    while True:
        schedule.run_pending()
        time.sleep(1)


def is_valid_time(time: str) -> bool:
    return bool(re.match(r"^\d{2}:\d{2}(:\d{2})?$", time))


@click.command()
@click.argument("handle")
@click.option("-p", "--topic", required=True, help="ntfy topic")
@click.option(
    "-t", "--times", multiple=True, default=["09:00", "21:00"], show_default=True
)
@click.option("--url", default=nfty, show_default=True)
@click.option("-i", "--imediate", is_flag=True, help="run immediately")
def cli(handle: str, topic: str, times: list[str], url: str, imediate: bool) -> None:
    info = NotiInfo(handle=handle, topic=topic, url=url)

    if imediate:
        loop(info)
        return

    valid_times = [t for t in times if is_valid_time(t)]
    if not valid_times:
        msg = f"invalid times: {times:!r}"
        raise ValueError(msg)
    main(info, valid_times)


if __name__ == "__main__":
    cli()
