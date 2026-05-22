"""
myTischtennis Data Fetcher
Holt Daten über die HTML-Seite (wie manuell getestet) + öffentliche API-Endpunkte
"""

import requests
import json
import os
import re
from datetime import datetime

EMAIL    = os.environ.get("MYTT_EMAIL", "")
PASSWORD = os.environ.get("MYTT_PASSWORD", "")

NUID         = "NU2769890"
CLUB_NR      = "03024"
ORGANIZATION = "TTBW"
SEASON       = "25-26"

TEAMS = [
    {"id": "2961473", "group_id": "494308", "name": "Erwachsene KLB"},
    {"id": "2961739", "group_id": "500517", "name": "Senioren 40"},
]

SUPABASE_URL = "https://supabase.mytischtennis.de"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzYiIsInJvbGUiOiJhbm9uIiwiZXhwIjo5OTk5OTk5OTk5fQ.uuv5nJLBPFYbi2gSnxzPZ1jOPwV9rDZKTKBQDFAhXnE"
BASE_URL     = "https://www.mytischtennis.de"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})

def save(name, data):
    os.makedirs("data", exist_ok=True)
    path = f"data/{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  💾 {path}")

def login():
    print("🔐 Einloggen...")
    res = session.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
        json={"email": EMAIL, "password": PASSWORD},
    )
    if res.status_code != 200:
        raise ValueError(f"Login fehlgeschlagen: {res.status_code} {res.text[:200]}")
    data = res.json()
    token = data.get("access_token", "")
    if not token:
        raise ValueError(f"Kein Token in Antwort: {data}")
    # Cookie setzen
    session.cookies.set("sb-10-auth-token", token, domain="mytischtennis.de")
    session.cookies.set("sb-10-auth-token", token, domain="www.mytischtennis.de")
    print(f"  ✅ Eingeloggt als {data.get('user', {}).get('email', '?')}")
    return token

def fetch_ttr_history_from_page():
    """Holt TTR-Historie direkt aus der HTML-Seite (wie manuell getestet)"""
    print("📈 TTR-Historie (via HTML-Seite)...")
    res = session.get(f"{BASE_URL}/rankings/ttr-historie?show=everything")
    if res.status_code != 200:
        raise ValueError(f"Seite nicht erreichbar: {res.status_code}")
    
    html = res.text
    
    # Extrahiere JSON-Daten aus __remixContext (wie im Browser)
    # Suche nach dem ttr_history block
    pattern = r'__remixContext\.r\("routes/\$",\s*"[^"]+\|data",\s*(\{[^<]+?"formattedMaxTtrDate"[^}]+\})'
    matches = re.findall(pattern, html, re.DOTALL)
    
    if not matches:
        # Fallback: suche nach dem event array
        pattern2 = r'"ttr":\s*\d+,\s*"event":\s*\['
        if pattern2 in html or re.search(pattern2, html):
            # Extrahiere größeren Block
            idx = html.find('"person_id": "NU2769890"')
            if idx == -1:
                idx = html.find(f'"person_id":"{NUID}"')
            if idx > 0:
                # Finde den Anfang des JSON-Objekts
                start = html.rfind('__remixContext.r(', 0, idx)
                if start > 0:
                    # Extrahiere bis zum Ende
                    chunk = html[start:start+50000]
                    # Finde JSON-Start
                    json_start = chunk.find('{')
                    json_chunk = chunk[json_start:]
                    # Finde Ende (vor dem closing parenthesis)
                    depth = 0
                    end = 0
                    for i, c in enumerate(json_chunk):
                        if c == '{': depth += 1
                        elif c == '}':
                            depth -= 1
                            if depth == 0:
                                end = i + 1
                                break
                    if end > 0:
                        try:
                            data = json.loads(json_chunk[:end])
                            save("ttr_history", data)
                            print(f"  ✅ {len(data.get('event', []))} Ereignisse gefunden")
                            return data
                        except json.JSONDecodeError as e:
                            print(f"  ⚠️  JSON parse error: {e}")
    
    if matches:
        try:
            data = json.loads(matches[0])
            save("ttr_history", data)
            print(f"  ✅ {len(data.get('event', []))} Ereignisse gefunden")
            return data
        except json.JSONDecodeError as e:
            print(f"  ⚠️  JSON parse error: {e}")
    
    print("  ⚠️  Konnte keine TTR-Daten extrahieren")
    # Debug: speichere HTML
    with open("data/debug_html.txt", "w") as f:
        f.write(html[:5000])
    print("  ℹ️  Debug-HTML gespeichert")
    return None

def fetch_public(url, params=None):
    res = session.get(url, params=params)
    if res.status_code == 200:
        try:
            return res.json()
        except:
            return None
    return None

def fetch_team_data():
    for team in TEAMS:
        print(f"📅 Spielplan: {team['name']}...")
        data = fetch_public(f"{BASE_URL}/api/ttr/team/schedule",
                           params={"teamId": team["id"], "season": SEASON})
        if data:
            save(f"schedule_{team['id']}", data)
            print(f"  ✅ Gespeichert")
        else:
            print(f"  ⚠️  Nicht verfügbar")

        print(f"📋 Tabelle: {team['name']}...")
        # Verschiedene Endpunkt-Varianten probieren
        for url in [
            f"{BASE_URL}/api/league-table/{ORGANIZATION}/{team['group_id']}",
            f"{BASE_URL}/api/click-tt/{ORGANIZATION}/leagues/{team['group_id']}/table",
        ]:
            data = fetch_public(url)
            if data:
                save(f"table_{team['group_id']}", data)
                print(f"  ✅ Gespeichert ({url})")
                break
        else:
            print(f"  ⚠️  Tabelle nicht verfügbar")

def save_meta():
    meta = {
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "nuid": NUID,
        "club": CLUB_NR,
        "organization": ORGANIZATION,
        "season": SEASON,
        "teams": TEAMS,
    }
    save("meta", meta)

if __name__ == "__main__":
    if not EMAIL or not PASSWORD:
        print("⚠️  MYTT_EMAIL / MYTT_PASSWORD nicht gesetzt")
        raise SystemExit(1)

    login()
    fetch_ttr_history_from_page()
    fetch_team_data()
    save_meta()
    print("\n✅ Fertig!")
