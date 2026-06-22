# Punktlich-Fix: Schritt fuer Schritt

Reihenfolge einhalten. Dauer insgesamt ca. 15 Minuten.

==================================================
SCHRITT 1  -  Dateien ins Repo deployen (1 Befehl)
==================================================
1. Dieses Zip komplett in einen Ordner entpacken.
2. In diesem Ordner Rechtsklick, "In Terminal oeffnen", oder PowerShell oeffnen und hineinwechseln.
3. Falls PowerShell die Ausfuehrung blockt, einmal dieses voranstellen:
       powershell -ExecutionPolicy Bypass -File .\deploy-fix.ps1
   sonst einfach:
       .\deploy-fix.ps1
4. Liegt dein Repo nicht im Standardpfad, gib ihn mit an:
       .\deploy-fix.ps1 -Repo "C:\dein\pfad\zum\repo"

Erwartung: am Ende steht "FERTIG. Dateien deployed und gepusht."
Damit sind post.py, post.yml und refresh-token.yml im Repo.

==================================================
SCHRITT 2  -  Token (PAT) erstellen
==================================================
Wir nehmen den klassischen PAT, der loest workflow_dispatch zuverlaessig aus
und darf gleichzeitig das Token-Secret aktualisieren. Ein Token fuer beide Jobs.

1. GitHub oeffnen, oben rechts auf dein Profilbild, Settings.
2. Ganz unten links: Developer settings.
3. Personal access tokens, dann "Tokens (classic)".
4. Generate new token, Variante "Generate new token (classic)".
5. Note: TTM Automation. Expiration: 1 year (oder No expiration fuer dauerhaft).
6. Scopes anhaken:
     [x] repo            (komplett, der oberste Haken deckt alles darunter)
     [x] workflow
7. Generate token. Den Token JETZT kopieren, er wird nur einmal gezeigt.

==================================================
SCHRITT 3  -  Token als Secret hinterlegen
==================================================
Damit der naechtliche Token-Refresh das IG-Secret schreiben darf.
1. Dein Repo auf GitHub oeffnen.
2. Settings (Reiter oben im Repo, nicht das Profil-Settings).
3. Links: Secrets and variables, dann Actions.
4. New repository secret.
5. Name:  GH_PAT
   Secret: den in Schritt 2 kopierten Token einfuegen.
6. Add secret.

==================================================
SCHRITT 4  -  Externer Ausloeser bei cron-job.org
==================================================
Das ersetzt GitHubs traegen Zeitplan durch einen puenktlichen Ausloeser.
1. cron-job.org oeffnen, kostenlos registrieren, einloggen.
2. "Create cronjob" (oder das Plus-Symbol).
3. Title: TTM Poster
4. URL (genau so, eine Zeile):
   https://api.github.com/repos/TimRich2025/thethoughtfulman/actions/workflows/post.yml/dispatches
5. Den Bereich "Advanced" oder "Erweitert" aufklappen.
6. Request method: POST
7. Request body / Body:
   {"ref":"main"}
8. Custom HTTP headers, vier Zeilen hinzufuegen (Name, Wert):
   Accept                 application/vnd.github+json
   Authorization          Bearer DEIN_TOKEN_AUS_SCHRITT_2
   X-GitHub-Api-Version   2022-11-28
   Content-Type           application/json
9. Schedule: every 5 minutes. (Im Zeitplan jede Minute durch 5 teilbar, oder "*/5".)
   Timezone Europe/Berlin.
10. Speichern. Dann oben "TEST RUN" druecken.
    Erwartung: Response status 204. 204 heisst Erfolg, GitHub hat den Lauf angenommen.
    Kommt 401 oder 403: Token in Authorization falsch oder Scope fehlt, Schritt 2 pruefen.

==================================================
SCHRITT 5  -  Testen
==================================================
1. Dein Repo, Reiter Actions.
2. Links Workflow "post", rechts "Run workflow", Branch main, bestaetigen.
3. Nach ein bis zwei Minuten sollte das aktuell faellige Reel auf
   @the.thoughtfulman online sein, und der Lauf gruen.
4. Ab jetzt feuert cron-job.org alle 5 Minuten. Da deine Slots auf :00 und :30
   liegen, trifft jeder Post seinen Slot auf die Minute.

==================================================
WAS JETZT LAEUFT
==================================================
- Ausloeser kommt puenktlich von cron-job.org statt vom traegen GitHub-Scheduler.
- post.py postet nur im 45-Minuten-Fenster um den Slot, sonst gilt der Slot als
  verpasst und du bekommst automatisch ein GitHub-Issue. Nie wieder Post zur Unzeit.
- refresh-token.yml frischt den IG-Token taeglich auf, er kann nicht mehr ablaufen.
- Toleranz aendern: in .github/workflows/post.yml die Zeile LATE_WINDOW_MIN anpassen.

==================================================
WENN ETWAS HAKT
==================================================
- cron-job.org Test gibt 403: PAT-Scope. Muss klassischer PAT mit "repo" (und "workflow") sein.
- Run workflow rot beim Schritt "faelliges reel veroeffentlichen": IG-Token pruefen.
- Kein Lauf startet trotz cron-job.org: in cron-job.org pruefen ob der Job aktiv (enabled) ist
  und die letzte Ausfuehrung 204 lieferte.
