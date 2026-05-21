# 🏓 myTischtennis Statistik-Website

Persönliche Statistik-Website mit automatischer Datensynchronisation von myTischtennis.de.

## Setup (einmalig, ~10 Minuten)

### 1. Repository erstellen
- Neues GitHub-Repository anlegen, z.B. `mytt-stats`
- Diese Dateien reinkopieren / hochladen

### 2. Secrets hinterlegen
GitHub → Repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Name | Wert |
|------|------|
| `MYTT_EMAIL` | deine myTischtennis E-Mail |
| `MYTT_PASSWORD` | dein myTischtennis Passwort |

### 3. GitHub Pages aktivieren
GitHub → Repository → **Settings** → **Pages**
- Source: `Deploy from a branch`
- Branch: `main` / Ordner: `/ (root)`
- Speichern

### 4. Ersten Datenabruf starten
GitHub → Repository → **Actions** → **Daten aktualisieren** → **Run workflow**

Nach ~1 Minute sind die Daten da und die Website ist live unter:
`https://DEIN-USERNAME.github.io/REPO-NAME/`

---

## Automatische Updates

GitHub Actions läuft täglich um 06:00 UTC und aktualisiert alle Daten automatisch.
Manuell auslösen: Actions → Daten aktualisieren → Run workflow

---

## Lokale Entwicklung

```bash
pip install requests
python fetch_data.py   # einmalig Daten holen
# dann index.html im Browser öffnen (via lokalem Server, z.B. python -m http.server)
```

---

## Datenquellen

| Datei | Endpunkt | Auth |
|-------|----------|------|
| `data/ttr_history.json` | `/api/ttr/history/{nuid}` | ✅ |
| `data/match_stats.json` | `/api/statistics/{nuid}/matches/current_season` | ✅ |
| `data/schedule_{teamId}.json` | `/api/ttr/team/schedule` | ❌ |
| `data/table_{groupId}.json` | `/api/league-table/{org}/{group}` | ❌ |
| `data/players_{teamId}.json` | `/api/ttr/team/players` | ❌ |
