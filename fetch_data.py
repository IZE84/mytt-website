"""
myTischtennis Data Fetcher
Holt alle relevanten Daten und speichert sie als JSON in /data/
"""

import requests
import json
import os
from datetime import datetime

# ── Konfiguration ────────────────────────────────────────────────────────────
EMAIL    = os.environ.get("MYTT_EMAIL", "")
PASSWORD = os.environ.get("MYTT_PASSWORD", "")

NUID         = "NU2769890"
CLUB_NR      = "03024"
ORGANIZATION = "TTBW"
SEASON       = "25--26"

# Beide Mannschaften
TEAMS = [
    {"id": "2961473", "group_id": "494308", "name": "Erwachsene KLB"},
    {"id": "2961739", "group_id": "500517", "name": "Senioren 40"},
]

SUPABASE_URL = "https://supabase.mytischtennis.de"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzYiIsInJvbGUiOiJhbm9uIiwiZXhwIjo5OTk5OTk5OTk5fQ.uuv5nJLBPFYbi2gSnxzPZ1jOPwV9rDZKTKBQDFAhXnE"
BASE_URL     = "https://www.mytischtennis.de"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

# ── Login ────────────────────────────────────────────────────────────────────
def login():
    print("🔐 Einloggen...")
    res = session.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
        json={"email": EMAIL, "password": PASSWORD},
    )
    res.raise_for_status()
    data = res.json()
    token = data.get("access_token", "")
    if not token:
        raise ValueError("Login fehlgeschlagen – Token leer")
    session.cookies.set("sb-10-auth-token", token, domain="www.mytischtennis.de")
    print("✅ Eingeloggt")
    return token


# ── Daten holen ──────────────────────────────────────────────────────────────
def fetch(url, **kwargs):
    res = session.get(url, **kwargs)
    res.raise_for_status()
    return res.json()


def save(name, data):
    os.makedirs("data", exist_ok=True)
    path = f"data/{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 {path}")


# ── Einzelne Endpunkte ───────────────────────────────────────────────────────
def fetch_ttr_history():
    print("📈 TTR-Historie...")
    data = fetch(f"{BASE_URL}/api/ttr/history/{NUID}")
    save("ttr_history", data)
    return data


def fetch_match_stats(date_range="current_season"):
    print("📊 Match-Statistiken...")
    try:
        data = fetch(f"{BASE_URL}/api/statistics/{NUID}/matches/{date_range}")
        save("match_stats", data)
    except Exception as e:
        print(f"  ⚠️  Match-Stats nicht verfügbar: {e}")


def fetch_team_schedule(team):
    print(f"📅 Spielplan: {team['name']}...")
    try:
        data = fetch(
            f"{BASE_URL}/api/ttr/team/schedule",
            params={"teamId": team["id"], "season": SEASON},
        )
        save(f"schedule_{team['id']}", data)
    except Exception as e:
        print(f"  ⚠️  Spielplan nicht verfügbar: {e}")


def fetch_league_table(team):
    print(f"📋 Tabelle: {team['name']}...")
    try:
        data = fetch(f"{BASE_URL}/api/league-table/{ORGANIZATION}/{team['group_id']}")
        save(f"table_{team['group_id']}", data)
    except Exception as e:
        print(f"  ⚠️  Tabelle nicht verfügbar: {e}")


def fetch_team_balances(team):
    print(f"⚖️  Bilanzen: {team['name']}...")
    try:
        data = fetch(
            f"{BASE_URL}/api/ttr/team/players",
            params={"teamId": team["id"]},
        )
        save(f"players_{team['id']}", data)
    except Exception as e:
        print(f"  ⚠️  Bilanzen nicht verfügbar: {e}")


# ── Meta-Datei ───────────────────────────────────────────────────────────────
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


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if EMAIL and PASSWORD:
        login()
        fetch_ttr_history()
        fetch_match_stats()
    else:
        print("⚠️  Keine Credentials – nur öffentliche Daten")

    for team in TEAMS:
        fetch_team_schedule(team)
        fetch_league_table(team)
        fetch_team_balances(team)

    save_meta()
    print("\n✅ Fertig!")
