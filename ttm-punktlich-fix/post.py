#!/usr/bin/env python3
"""
TheThoughtfulman Auto-Poster
Postet faellige Reels aus queue.csv ueber die Instagram Graph API (Instagram Login).
Faelligkeit wird in Europe/Berlin geprueft. Pro Lauf hoechstens EIN Reel.

NEU: harte Zeitsperre. Ist ein faelliges Reel mehr als LATE_WINDOW_MIN Minuten
zu spaet, wird es NICHT zur Unzeit nachgeschoben, sondern als 'missed' markiert
und der Lauf endet mit Fehlercode, damit der Alarm anschlaegt. So geht nie wieder
etwas Stunden nach Plan raus.
"""
import csv, os, sys, time
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

TZ              = ZoneInfo("Europe/Berlin")
API             = "https://graph.instagram.com/v22.0"
QUEUE           = "queue.csv"
TOKEN           = os.environ["IG_ACCESS_TOKEN"]
IG_ID           = os.environ["IG_USER_ID"]
REPO            = os.environ.get("GITHUB_REPOSITORY", "")
BRANCH          = os.environ.get("GITHUB_REF_NAME", "main")
LATE_WINDOW_MIN = int(os.environ.get("LATE_WINDOW_MIN", "45"))  # Slot-Toleranz in Minuten

def raw_url(reel):
    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/reels/{reel}"

def jsdelivr_url(reel):
    return f"https://cdn.jsdelivr.net/gh/{REPO}@{BRANCH}/reels/{reel}"

def create_container(video_url, caption):
    r = requests.post(f"{API}/{IG_ID}/media", data={
        "media_type": "REELS", "video_url": video_url, "caption": caption,
        "share_to_feed": "true", "thumb_offset": "3000", "access_token": TOKEN,
    }, timeout=180)
    j = r.json()
    if "id" not in j:
        raise RuntimeError(f"Container abgelehnt: {r.status_code} {j}")
    return j["id"]

def wait_finished(cid, tries=40, delay=10):
    last = None
    for _ in range(tries):
        r = requests.get(f"{API}/{cid}", params={"fields": "status_code", "access_token": TOKEN}, timeout=60)
        last = r.json(); sc = last.get("status_code")
        if sc == "FINISHED": return
        if sc == "ERROR": raise RuntimeError(f"Verarbeitung fehlgeschlagen: {last}")
        time.sleep(delay)
    raise RuntimeError(f"Timeout bei Verarbeitung: {last}")

def publish(cid):
    r = requests.post(f"{API}/{IG_ID}/media_publish", data={"creation_id": cid, "access_token": TOKEN}, timeout=120)
    j = r.json()
    if "id" not in j:
        raise RuntimeError(f"Publish fehlgeschlagen: {r.status_code} {j}")
    return j["id"]

def post_reel(reel, caption):
    last = None
    for url in (raw_url(reel), jsdelivr_url(reel)):
        try:
            cid = create_container(url, caption); wait_finished(cid); return publish(cid)
        except RuntimeError as e:
            print(f"  Quelle {url.split('/')[2]} fehlgeschlagen: {e}"); last = e
    raise last

def load_rows():
    with open(QUEUE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f); fields = list(reader.fieldnames); rows = list(reader)
    if "posted_at" not in fields: fields.append("posted_at")
    return rows, fields

def save_rows(rows, fields):
    with open(QUEUE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in rows:
            r.setdefault("posted_at", ""); w.writerow(r)

def main():
    if not REPO:
        print("GITHUB_REPOSITORY fehlt"); sys.exit(1)
    rows, fields = load_rows()
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
    missed, postable = [], []
    for dt, i in due:
        late_min = (now - dt).total_seconds() / 60.0
        (missed if late_min > LATE_WINDOW_MIN else postable).append((dt, i, late_min))

    changed = False
    for dt, i, late_min in missed:
        rows[i]["status"] = "missed"; rows[i].setdefault("posted_at", "")
        print(f"VERPASST: {rows[i]['reel'].strip()} (geplant {rows[i]['scheduled_berlin']}) war {int(late_min)} min zu spaet, Fenster ist {LATE_WINDOW_MIN}. NICHT gepostet, als 'missed' markiert.")
        changed = True

    if postable:
        idx = postable[0][1]; row = rows[idx]
        caption = (row.get("caption") or "").rstrip()
        tags = (row.get("hashtags") or "").strip()
        full = caption + ("\n\n" + tags if tags else "")
        reel = row["reel"].strip()
        print(f"Poste {reel} (geplant {row['scheduled_berlin']} Berlin, jetzt {now:%H:%M}) ...")
        mid = post_reel(reel, full)
        print(f"Veroeffentlicht: media_id={mid}")
        row["status"] = "posted"; row["posted_at"] = f"{now:%Y-%m-%d %H:%M}"; changed = True
    else:
        print("Im erlaubten Zeitfenster ist nichts faellig.")

    if changed:
        save_rows(rows, fields)

    if missed:
        # sichtbar machen: Lauf rot faerben, damit der Alarm in post.yml ein Issue oeffnet
        sys.exit(2)

if __name__ == "__main__":
    main()
