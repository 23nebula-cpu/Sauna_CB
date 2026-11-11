#!/usr/bin/env python3
"""Log KSZCB sauna occupancy and plot it.

  python sauna.py log    # fetch once, append to sauna_log.csv
  python sauna.py plot   # make sauna_log.png from the CSV

Cron (every 30 min):
  */30 * * * * /usr/bin/python3 /path/to/sauna.py log
"""
import csv, re, sys, urllib.request
from datetime import datetime
from pathlib import Path

URL = "https://www.kszcb.cz/sauna"
CSV = Path(__file__).with_name("sauna_log.csv")
PNG = Path(__file__).with_name("sauna_log.png")


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    m = re.search(r"(\d+)\s*%\s*Obsazenost\s*(\d+)\s*/\s*(\d+)", text)
    if not m:
        raise RuntimeError("Occupancy not found in page (layout changed or loaded by JS)")
    return int(m[1]), int(m[2]), int(m[3])


def log():
    pct, now, cap = fetch()
    new = not CSV.exists()
    with CSV.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "percent", "people", "capacity"])
        w.writerow([datetime.now().isoformat(timespec="minutes"), pct, now, cap])
    print(datetime.now().isoformat(timespec="minutes"), pct, now, cap)


def plot():
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    t, p = [], []
    with CSV.open() as f:
        for r in csv.DictReader(f):
            t.append(datetime.fromisoformat(r["timestamp"]))
            p.append(int(r["percent"]))
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(t, p, marker="o", ms=3, lw=1.2)
    ax.set_ylabel("Occupancy (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Sauna České Budějovice – obsazenost")
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%a %d.%m %H:%M"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(PNG, dpi=150)
    print("Saved", PNG)


if __name__ == "__main__":
    {"log": log, "plot": plot}.get(sys.argv[1] if len(sys.argv) > 1 else "", log)()
