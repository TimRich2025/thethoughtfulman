#!/usr/bin/env python3
"""
TheThoughtfulman Auto-Poster
Postet faellige Reels aus queue.csv ueber die Instagram Graph API (Instagram Login).
Die Faelligkeit wird in Europe/Berlin geprueft, nicht in UTC. Damit ist der
Sommer/Winterzeit-Drift erledigt. Pro Lauf wird hoechstens EIN Reel
veroeffentlicht (das aelteste faellige), damit ein Rueckstand nicht auf
einmal rausgeballert wird.
"""
import csv, os, sys, time
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

TZ     = ZoneInfo("Europe/Berlin")
API    = "https://graph.instagram.com/v22.0"
QUEUE  = "queue.csv"
TOKEN  = os.environ["IG_ACCESS_TOKEN"]
IG_ID  = os.environ["IG_USER_ID"]
REPO   = os.environ.get("GITHUB_REPOSITORY", "")   # z.B. timroelz/thethoughtfulman
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")

def raw_url(reel):
    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/reels/{reel}"

def jsdelivr_url(reel):
    return f"https://cdn.jsdelivr.net/gh/{REPO}@{BRANCH}/reels/{reel}"

def create_container(video_url, caption):
    r = requests.post(f"{API}/{IG_ID}/media", data={
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": "true",
        "thumb_offset": "3000",   # Cover aus der Mitte, nicht das schwarze Erstbild
        "access_token": TOKEN,
    }, timeout=180)
    j = r.json()
    if "id" not in j:
        raise RuntimeError(f"Container abgelehnt: {r.status_code} {j}")
    return j["id"]

def wait_finished(cid, tries=40, delay=10):
    last = None
    for _ in range(tries):
        r = requests.get(f"{API}/{cid}", params={
            "fields": "status_code", "access_token": TOKEN}, timeout=60)
        last = r.json()
        sc = last.get("status_code")
        if sc == "FINISHED":
            return
        if sc == "ERROR":
            raise RuntimeError(f"Verarbeitung fehlgeschlagen: {last}")
        time.sleep(delay)
    raise RuntimeError(f"Timeout bei Verarbeitung: {last}")

def publish(cid):
    r = requests.post(f"{API}/{IG_ID}/media_publish", data={
        "creation_id": cid, "access_token": TOKEN}, timeout=120)
    j = r.json()
    if "id" not in j:
        raise RuntimeError(f"Publish fehlgeschlagen: {r.status_code} {j}")
    return j["id"]

def post_reel(reel, caption):
    # erst raw GitHub, bei Problemen einmal ueber jsDelivr CDN
    last = None
    for url in (raw_url(reel), jsdelivr_url(reel)):
        try:
            cid = create_container(url, caption)
            wait_finished(cid)
            return publish(cid)
        except RuntimeError as e:
            print(f"  Quelle {url.split('/')[2]} fehlgeschlagen: {e}")
            last = e
    raise last

def main():
    if not REPO:
        print("GITHUB_REPOSITORY fehlt"); sys.exit(1)
    with open(QUEUE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames)
        rows = list(reader)
    if "posted_at" not in fields:
        fields.append("posted_at")

    now = datetime.now(TZ)
    due = []
    for i, row in enumerate(rows):
        if (row.get("status") or "").strip().lower() != "pending":
            continue
        try:
            dt = datetime.strptime(row["scheduled_berlin"].strip(), "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
        except (ValueError, KeyError):
            continue
        if dt <= now:
            due.append((dt, i))

    if not due:
        print(f"{now:%Y-%m-%d %H:%M} Berlin: nichts faellig.")
        return

    due.sort()
    idx = due[0][1]
    row = rows[idx]
    caption = (row.get("caption") or "").rstrip()
    tags = (row.get("hashtags") or "").strip()
    full = caption + ("\n\n" + tags if tags else "")
    reel = row["reel"].strip()

    print(f"Poste {reel} (geplant {row['scheduled_berlin']} Berlin) ...")
    mid = post_reel(reel, full)
    print(f"Veroeffentlicht: media_id={mid}")

    row["status"] = "posted"
    row["posted_at"] = f"{now:%Y-%m-%d %H:%M}"
    with open(QUEUE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            r.setdefault("posted_at", "")
            w.writerow(r)

if __name__ == "__main__":
    main()
