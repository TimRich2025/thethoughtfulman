# TheThoughtfulman Auto-Poster

## Der einfachste Weg (eine Zeile)
1. Dieses Zip entpacken.
2. Im entpackten Ordner Rechtsklick, "In Terminal oeffnen" (oder PowerShell, dann mit cd hineinwechseln).
3. Diese eine Zeile eingeben:
       powershell -ExecutionPolicy Bypass -File .\deploy.ps1
Das Skript laedt alles hoch, aktiviert den Zeitplan und loest den ersten Reel aus.

Voraussetzung (hast du vom letzten Mal schon): GitHub CLI und Git installiert und einmal `gh auth login`.
Falls dein Repo anders heisst als "thethoughtfulman":
       powershell -ExecutionPolicy Bypass -File .\deploy.ps1 -RepoName DEIN-REPO-NAME

## Was es tut
post.py prueft die Faelligkeit in Europe/Berlin (nicht UTC), darum stimmt die Zeit jetzt,
inklusive Sommer/Winterzeit. Pro Lauf wird hoechstens ein Reel veroeffentlicht.
queue.csv enthaelt alle 14 Reels mit Zeitstempel, Caption und Hashtags.

## Naechste Woche
Neue Zeilen unten an queue.csv anhaengen (status = pending), neue Videos nach reels/ legen,
dann deploy.ps1 nochmal ausfuehren.

## Wartung
Instagram-Token laeuft nach ca. 60 Tagen ab. Dann einmal:
    gh secret set IG_ACCESS_TOKEN --body DEIN_NEUES_TOKEN
