from flask import Flask, render_template_string, jsonify, request
import sqlite3
import json
from datetime import datetime
import os

app = Flask(__name__)

# Базы данных для двух серверов
DB_NETHEROP = "netherop_tiers.db"
DB_BEAST = "beast_tiers.db"


# Функция для создания базы данных (НЕ УДАЛЯЕТ существующие)
def init_db(db_path):
    # Проверяем существует ли база данных
    db_exists = os.path.exists(db_path)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS players
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  discord_id TEXT UNIQUE,
                  username TEXT,
                  tier TEXT,
                  sub_tier TEXT,
                  updated_at TIMESTAMP)""")
    conn.commit()
    conn.close()

    if db_exists:
        print(f"[INFO] База данных {db_path} уже существует, данные сохранены")
    else:
        print(f"[INFO] База данных {db_path} создана (новая)")


# Инициализируем базы данных (без удаления)
init_db(DB_NETHEROP)
init_db(DB_BEAST)

# Очки за подтиры для NetherOP
SUB_TIER_POINTS_NETHEROP = {
    "HT1": 10,
    "LT1": 8,
    "HT2": 7,
    "LT2": 6,
    "HT3": 5,
    "LT3": 4,
    "HT4": 3,
    "LT4": 2,
    "HT5": 1,
    "LT5": 1,
}

# Очки за подтиры для Beast
SUB_TIER_POINTS_BEAST = {
    "HT1": 10,
    "LT1": 8,
    "HT2": 7,
    "LT2": 6,
    "HT3": 5,
    "LT3": 4,
    "HT4": 3,
    "LT4": 2,
    "HT5": 1,
    "LT5": 1,
}


def truncate_name(name, max_len=10):
    if len(name) > max_len:
        return name[:max_len] + "..."
    return name


def update_player(db_path, discord_id, username, tier, sub_tier):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """INSERT OR REPLACE INTO players (discord_id, username, tier, sub_tier, updated_at)
                 VALUES (?, ?, ?, ?, ?)""",
        (str(discord_id), username, tier, sub_tier, datetime.now()),
    )
    conn.commit()
    conn.close()
    print(f"[БД] Обновлён: {username} -> {tier} ({sub_tier})")


def remove_player(db_path, discord_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM players WHERE discord_id = ?", (str(discord_id),))
    conn.commit()
    conn.close()
    print(f"[БД] Удалён: {discord_id}")


# API для NetherOP
@app.route("/api/players/netherop")
def get_players_netherop():
    conn = sqlite3.connect(DB_NETHEROP)
    c = conn.cursor()
    c.execute("SELECT username, tier, sub_tier FROM players")
    players = {}
    for username, tier, sub_tier in c.fetchall():
        if tier not in players:
            players[tier] = []
        players[tier].append({"username": username, "sub_tier": sub_tier})
    conn.close()
    return jsonify(players)


@app.route("/api/leaderboard/netherop")
def get_leaderboard_netherop():
    conn = sqlite3.connect(DB_NETHEROP)
    c = conn.cursor()
    c.execute("SELECT username, sub_tier FROM players")
    players_data = []
    for username, sub_tier in c.fetchall():
        points = SUB_TIER_POINTS_NETHEROP.get(sub_tier, 0)
        players_data.append(
            {"username": username, "sub_tier": sub_tier, "points": points}
        )
    conn.close()
    players_data.sort(key=lambda x: x["points"], reverse=True)
    return jsonify(players_data[:25])


# API для Beast
@app.route("/api/players/beast")
def get_players_beast():
    conn = sqlite3.connect(DB_BEAST)
    c = conn.cursor()
    c.execute("SELECT username, tier, sub_tier FROM players")
    players = {}
    for username, tier, sub_tier in c.fetchall():
        if tier not in players:
            players[tier] = []
        players[tier].append({"username": username, "sub_tier": sub_tier})
    conn.close()
    return jsonify(players)


@app.route("/api/leaderboard/beast")
def get_leaderboard_beast():
    conn = sqlite3.connect(DB_BEAST)
    c = conn.cursor()
    c.execute("SELECT username, sub_tier FROM players")
    players_data = []
    for username, sub_tier in c.fetchall():
        points = SUB_TIER_POINTS_BEAST.get(sub_tier, 0)
        players_data.append(
            {"username": username, "sub_tier": sub_tier, "points": points}
        )
    conn.close()
    players_data.sort(key=lambda x: x["points"], reverse=True)
    return jsonify(players_data[:25])


# API для общего Leaderboard (объединяем по никам)
@app.route("/api/leaderboard/all")
def get_leaderboard_all():
    players_dict = {}

    # Собираем NetherOP игроков
    conn = sqlite3.connect(DB_NETHEROP)
    c = conn.cursor()
    c.execute("SELECT username, sub_tier FROM players")
    for username, sub_tier in c.fetchall():
        points = SUB_TIER_POINTS_NETHEROP.get(sub_tier, 0)
        if username not in players_dict:
            players_dict[username] = {
                "username": username,
                "total_points": 0,
                "op_tier": None,
                "beast_tier": None,
                "op_points": 0,
                "beast_points": 0,
            }
        players_dict[username]["total_points"] += points
        players_dict[username]["op_tier"] = sub_tier
        players_dict[username]["op_points"] = points
    conn.close()

    # Собираем Beast игроков
    conn = sqlite3.connect(DB_BEAST)
    c = conn.cursor()
    c.execute("SELECT username, sub_tier FROM players")
    for username, sub_tier in c.fetchall():
        points = SUB_TIER_POINTS_BEAST.get(sub_tier, 0)
        if username not in players_dict:
            players_dict[username] = {
                "username": username,
                "total_points": 0,
                "op_tier": None,
                "beast_tier": None,
                "op_points": 0,
                "beast_points": 0,
            }
        players_dict[username]["total_points"] += points
        players_dict[username]["beast_tier"] = sub_tier
        players_dict[username]["beast_points"] = points
    conn.close()

    # Преобразуем в список и сортируем по общим очкам
    players_list = list(players_dict.values())
    players_list.sort(key=lambda x: x["total_points"], reverse=True)

    # Добавляем ранги
    for i, player in enumerate(players_list):
        player["rank"] = i + 1

    return jsonify(players_list[:50])


# API для синхронизации из Discord бота
@app.route("/api/sync", methods=["POST"])
def sync_player():
    data = request.json
    action = data.get("action")
    server = data.get("server", "netherop")
    discord_id = data.get("discord_id")
    username = data.get("username")
    tier = data.get("tier")
    sub_tier = data.get("sub_tier")

    db_path = DB_NETHEROP if server == "netherop" else DB_BEAST

    if action == "add" and tier:
        update_player(db_path, discord_id, username, tier, sub_tier)
    elif action == "remove":
        remove_player(db_path, discord_id)

    return jsonify({"status": "ok"})


@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ARENATIERS - Тир-лист игроков</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Inter', sans-serif;
                background: #0a0c15;
                color: #ffffff;
                min-height: 100vh;
            }

            ::-webkit-scrollbar {
                width: 6px;
                height: 6px;
            }
            ::-webkit-scrollbar-track {
                background: #1a1d2e;
            }
            ::-webkit-scrollbar-thumb {
                background: #ff4655;
                border-radius: 3px;
            }

            .header {
                background: linear-gradient(180deg, #0f111a 0%, #0a0c15 100%);
                border-bottom: 1px solid rgba(255, 70, 85, 0.2);
                padding: 20px 0;
                position: sticky;
                top: 0;
                z-index: 100;
                backdrop-filter: blur(10px);
            }

            .header-content {
                max-width: 1400px;
                margin: 0 auto;
                padding: 0 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 20px;
            }

            .logo {
                font-family: 'Orbitron', monospace;
                font-size: 32px;
                font-weight: 800;
                background: linear-gradient(135deg, #ff4655, #ff8c42, #ff4655);
                background-size: 200% 200%;
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                letter-spacing: 2px;
                animation: gradientShift 3s ease infinite, glowPulse 2s ease-in-out infinite alternate;
            }

            @keyframes gradientShift {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }

            @keyframes glowPulse {
                from { text-shadow: 0 0 10px rgba(255, 70, 85, 0.3); }
                to { text-shadow: 0 0 30px rgba(255, 70, 85, 0.8), 0 0 10px rgba(255, 140, 66, 0.5); }
            }

            .nav {
                display: flex;
                gap: 10px;
                background: #1a1d2e;
                padding: 6px;
                border-radius: 50px;
            }

            .nav-btn {
                padding: 10px 24px;
                border-radius: 40px;
                font-weight: 600;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.3s ease;
                background: transparent;
                border: none;
                color: #8a8d9e;
                font-family: inherit;
            }

            .nav-btn.active {
                background: linear-gradient(135deg, #ff4655, #ff6b3d);
                color: white;
                box-shadow: 0 4px 15px rgba(255, 70, 85, 0.3);
            }

            .nav-btn:hover:not(.active) {
                color: white;
                background: rgba(255, 70, 85, 0.2);
            }

            .server-selector {
                display: flex;
                gap: 10px;
                background: #1a1d2e;
                padding: 6px;
                border-radius: 50px;
                transition: all 0.3s ease;
            }

            .server-selector.hidden {
                display: none;
            }

            .server-btn {
                padding: 10px 24px;
                border-radius: 40px;
                font-weight: 600;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.3s ease;
                background: transparent;
                border: none;
                color: #8a8d9e;
                font-family: inherit;
            }

            .server-btn.active {
                background: linear-gradient(135deg, #ff4655, #ff6b3d);
                color: white;
                box-shadow: 0 4px 15px rgba(255, 70, 85, 0.3);
            }

            .server-btn.beast.active {
                background: linear-gradient(135deg, #8b00ff, #4a00e0);
            }

            .server-btn:hover:not(.active) {
                color: white;
                background: rgba(255, 70, 85, 0.2);
            }

            .discord-dropdown {
                position: relative;
                display: inline-block;
            }

            .discord-main-btn {
                background: linear-gradient(135deg, #5865F2, #4752c4);
                border: none;
                padding: 10px 24px;
                border-radius: 40px;
                color: white;
                font-weight: 600;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.3s ease;
                font-family: inherit;
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .discord-main-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(88, 101, 242, 0.4);
            }

            .discord-dropdown-content {
                display: none;
                position: absolute;
                top: 100%;
                right: 0;
                margin-top: 10px;
                background: #1a1d2e;
                min-width: 200px;
                border-radius: 16px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.3);
                border: 1px solid rgba(255, 70, 85, 0.2);
                z-index: 200;
                overflow: hidden;
                animation: dropdownFade 0.3s ease;
            }

            @keyframes dropdownFade {
                from { opacity: 0; transform: translateY(-10px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .discord-dropdown-content.show {
                display: block;
            }

            .discord-server-item {
                padding: 12px 20px;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                gap: 12px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                font-size: 14px;
                font-weight: 500;
            }

            .discord-server-item:last-child {
                border-bottom: none;
            }

            .discord-server-item:hover {
                background: rgba(88, 101, 242, 0.2);
            }

            .discord-server-item i {
                width: 20px;
                color: #5865F2;
            }

            .search-container {
                position: relative;
            }

            .search-input {
                background: #1a1d2e;
                border: 1px solid rgba(255, 70, 85, 0.3);
                padding: 12px 20px 12px 45px;
                border-radius: 40px;
                color: white;
                font-size: 14px;
                width: 260px;
                transition: all 0.3s ease;
                font-family: inherit;
            }

            .search-input:focus {
                outline: none;
                border-color: #ff4655;
                width: 300px;
            }

            .search-input::placeholder {
                color: #5a5d6e;
            }

            .search-icon {
                position: absolute;
                left: 18px;
                top: 50%;
                transform: translateY(-50%);
                color: #5a5d6e;
            }

            .main-content {
                max-width: 1400px;
                margin: 0 auto;
                padding: 40px 30px;
            }

            .section {
                display: block;
            }

            .section.hidden {
                display: none;
            }

            .section-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
                flex-wrap: wrap;
                gap: 15px;
            }

            .section-title {
                font-family: 'Orbitron', monospace;
                font-size: 32px;
                font-weight: 700;
                letter-spacing: 1px;
                background: linear-gradient(135deg, #fff, #ff8c42);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }

            .tiers-horizontal {
                display: flex;
                flex-direction: row;
                gap: 20px;
                flex-wrap: wrap;
                justify-content: space-between;
            }

            .tier-card {
                flex: 1;
                min-width: 220px;
                background: #12141f;
                border-radius: 16px;
                overflow: hidden;
                border: 1px solid rgba(255, 70, 85, 0.15);
                transition: all 0.3s ease;
            }

            .tier-card:hover {
                transform: translateY(-5px);
                border-color: rgba(255, 70, 85, 0.4);
                box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            }

            .tier-card-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 18px 15px;
                background: linear-gradient(135deg, #1a1d2e, #12141f);
                border-bottom: 1px solid rgba(255, 70, 85, 0.2);
            }

            .tier-card-name {
                font-family: 'Orbitron', monospace;
                font-size: 18px;
                font-weight: 700;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .tier-card-count {
                background: rgba(255, 70, 85, 0.2);
                padding: 4px 10px;
                border-radius: 20px;
                font-size: 12px;
                color: #ff4655;
                font-weight: 600;
            }

            .tier-players-list {
                background: #0d0f18;
                display: block;
            }

            .players-list-vertical {
                display: flex;
                flex-direction: column;
                gap: 8px;
                padding: 15px;
            }

            .player-item {
                background: linear-gradient(135deg, #1a1d2e, #12141f);
                border: 1px solid rgba(255, 70, 85, 0.2);
                border-radius: 10px;
                padding: 8px 12px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                transition: all 0.3s ease;
                cursor: pointer;
            }

            .player-item:hover {
                transform: translateX(5px);
                border-color: #ff4655;
                background: linear-gradient(135deg, #22263a, #1a1d2e);
            }

            .player-name {
                font-size: 13px;
                font-weight: 500;
                color: #c0c8e0;
            }

            .player-subtier {
                font-size: 11px;
                font-weight: 600;
                padding: 3px 10px;
                border-radius: 20px;
                background: rgba(255, 70, 85, 0.2);
                color: #ff4655;
            }

            .empty-players {
                padding: 20px;
                text-align: center;
                color: #5a5d6e;
                font-style: italic;
                font-size: 13px;
            }

            .tier-1 { border-top: 3px solid #ffd700; }
            .tier-2 { border-top: 3px solid #c0c0c0; }
            .tier-3 { border-top: 3px solid #cd7f32; }
            .tier-4 { border-top: 3px solid #6c5ce7; }
            .tier-5 { border-top: 3px solid #00b894; }

            .tier-1 .tier-card-name { color: #ffd700; }
            .tier-2 .tier-card-name { color: #c0c0c0; }
            .tier-3 .tier-card-name { color: #cd7f32; }
            .tier-4 .tier-card-name { color: #6c5ce7; }
            .tier-5 .tier-card-name { color: #00b894; }

            .leaderboard-table {
                background: #12141f;
                border-radius: 16px;
                overflow: hidden;
                border: 1px solid rgba(255, 70, 85, 0.15);
            }

            .leaderboard-header {
                display: grid;
                grid-template-columns: 80px 1fr 180px 180px 100px;
                padding: 18px 25px;
                background: linear-gradient(90deg, #1a1d2e, #12141f);
                border-bottom: 1px solid rgba(255, 70, 85, 0.2);
                font-weight: 700;
                color: #8a8d9e;
                font-size: 14px;
            }

            .leaderboard-row {
                display: grid;
                grid-template-columns: 80px 1fr 180px 180px 100px;
                padding: 15px 25px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                transition: all 0.3s ease;
                align-items: center;
            }

            .leaderboard-row:hover {
                background: rgba(255, 70, 85, 0.05);
            }

            .rank { font-weight: 700; font-size: 18px; }
            .rank-1 { color: #ffd700; }
            .rank-2 { color: #c0c0c0; }
            .rank-3 { color: #cd7f32; }

            .player-points { font-weight: 700; font-size: 18px; color: #ff8c42; }

            .tier-column {
                text-align: center;
            }

            .tier-server-name {
                font-size: 11px;
                font-weight: 600;
                margin-bottom: 5px;
            }

            .tier-server-name.op {
                color: #ff4655;
            }

            .tier-server-name.beast {
                color: #8b00ff;
            }

            .tier-value {
                font-size: 14px;
                font-weight: 700;
                padding: 4px 12px;
                border-radius: 20px;
                display: inline-block;
            }

            .tier-value.op {
                background: rgba(255, 70, 85, 0.15);
                color: #ff4655;
                border: 1px solid rgba(255, 70, 85, 0.3);
            }

            .tier-value.beast {
                background: rgba(139, 0, 255, 0.15);
                color: #8b00ff;
                border: 1px solid rgba(139, 0, 255, 0.3);
            }

            .tier-empty {
                color: #5a5d6e;
                font-size: 12px;
                font-style: italic;
            }

            .queue-container {
                background: #12141f;
                border-radius: 16px;
                border: 1px solid rgba(255, 70, 85, 0.15);
                overflow: hidden;
            }

            .queue-section {
                padding: 30px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }

            .queue-section:last-child {
                border-bottom: none;
            }

            .queue-title {
                font-family: 'Orbitron', monospace;
                font-size: 22px;
                font-weight: 700;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .queue-title i {
                color: #ff4655;
                font-size: 28px;
            }

            .queue-text {
                color: #a0a3b5;
                line-height: 1.7;
                margin-bottom: 15px;
            }

            .cd-badge {
                background: rgba(255, 70, 85, 0.15);
                border: 1px solid rgba(255, 70, 85, 0.3);
                border-radius: 10px;
                padding: 12px 18px;
                display: inline-block;
                margin: 10px 0;
                color: #ff8c42;
                font-weight: 500;
            }

            .license-note {
                background: rgba(255, 140, 66, 0.1);
                border-radius: 10px;
                padding: 12px 18px;
                margin: 10px 0;
                color: #ff8c42;
            }

            .active-queue {
                background: linear-gradient(135deg, rgba(255, 70, 85, 0.1), rgba(255, 140, 66, 0.05));
                border-radius: 16px;
                padding: 25px;
                margin-top: 20px;
                border: 1px solid rgba(255, 70, 85, 0.3);
            }

            .queue-list {
                margin: 15px 0;
                padding-left: 20px;
            }

            .queue-list li {
                margin: 8px 0;
                color: #a0a3b5;
            }

            .mention {
                color: #ff4655;
                font-weight: 600;
            }

            .btn-join {
                background: linear-gradient(135deg, #ff4655, #ff6b3d);
                border: none;
                padding: 12px 28px;
                border-radius: 40px;
                color: white;
                font-weight: 600;
                cursor: pointer;
                margin-top: 15px;
                font-family: inherit;
            }

            .servers-buttons {
                display: flex;
                gap: 20px;
                margin-top: 20px;
                justify-content: center;
                flex-wrap: wrap;
            }

            .server-card {
                background: linear-gradient(135deg, #1a1d2e, #12141f);
                border-radius: 20px;
                padding: 20px 30px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
                border: 1px solid rgba(255, 70, 85, 0.2);
                min-width: 200px;
            }

            .server-card:hover {
                transform: translateY(-5px);
                border-color: #ff4655;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }

            .server-card.netherop:hover {
                border-color: #ff4655;
                box-shadow: 0 10px 30px rgba(255, 70, 85, 0.2);
            }

            .server-card.beast:hover {
                border-color: #8b00ff;
                box-shadow: 0 10px 30px rgba(139, 0, 255, 0.2);
            }

            .server-icon i {
                font-size: 32px;
                color: #5865F2;
            }

            .server-name {
                font-size: 20px;
                font-weight: 700;
                margin-bottom: 8px;
            }

            .server-card.netherop .server-name {
                color: #ff4655;
            }

            .server-card.beast .server-name {
                color: #8b00ff;
            }

            .server-desc {
                font-size: 12px;
                color: #8a8d9e;
            }

            .modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.85);
                backdrop-filter: blur(12px);
            }

            .modal-content {
                background: linear-gradient(135deg, #1a1d2e, #0f111a);
                margin: 10% auto;
                padding: 0;
                border: 1px solid rgba(255, 70, 85, 0.3);
                border-radius: 32px;
                width: 360px;
                position: relative;
                animation: modalFadeIn 0.3s ease;
                overflow: hidden;
            }

            @keyframes modalFadeIn {
                from { opacity: 0; transform: translateY(-30px) scale(0.95); }
                to { opacity: 1; transform: translateY(0) scale(1); }
            }

            .close-modal {
                position: absolute;
                top: 15px;
                right: 20px;
                color: #ff4655;
                font-size: 28px;
                cursor: pointer;
                transition: all 0.3s ease;
                z-index: 10;
            }

            .close-modal:hover {
                color: #ff8c42;
                transform: scale(1.1);
            }

            .modal-player-name {
                font-size: 28px;
                font-weight: 800;
                font-family: 'Orbitron', monospace;
                text-align: center;
                padding-top: 35px;
                margin-bottom: 10px;
                color: #fff;
                text-shadow: 0 0 10px #ff4655, 0 0 20px rgba(255, 70, 85, 0.5);
                animation: nameGlow 2s ease-in-out infinite alternate;
            }

            @keyframes nameGlow {
                from { text-shadow: 0 0 5px #ff4655; }
                to { text-shadow: 0 0 20px #ff4655, 0 0 10px #ff8c42; }
            }

            .modal-stats {
                display: flex;
                justify-content: center;
                gap: 40px;
                margin: 20px 0;
                padding: 0 20px;
            }

            .stat-item {
                text-align: center;
            }

            .stat-label {
                font-size: 11px;
                color: #8a8d9e;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 5px;
            }

            .stat-value {
                font-size: 24px;
                font-weight: 700;
                color: #ff8c42;
            }

            .modal-tiers-section {
                text-align: center;
                padding: 20px 20px 30px;
                border-top: 1px solid rgba(255, 70, 85, 0.2);
                margin-top: 10px;
            }

            .tiers-title {
                font-size: 12px;
                font-weight: 600;
                color: #ff4655;
                text-transform: uppercase;
                letter-spacing: 2px;
                margin-bottom: 15px;
            }

            .tiers-grid {
                display: flex;
                justify-content: center;
                gap: 20px;
                flex-wrap: wrap;
            }

            .tier-badge {
                padding: 8px 20px;
                border-radius: 40px;
                font-weight: 700;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.3s ease;
                position: relative;
            }

            .tier-badge.op {
                background: linear-gradient(135deg, rgba(255, 70, 85, 0.2), rgba(255, 107, 61, 0.1));
                border: 1px solid #ff4655;
                color: #ff4655;
            }

            .tier-badge.beast {
                background: linear-gradient(135deg, rgba(139, 0, 255, 0.2), rgba(74, 0, 224, 0.1));
                border: 1px solid #8b00ff;
                color: #8b00ff;
            }

            .tier-badge:hover {
                transform: scale(1.05);
            }

            .tier-tooltip {
                visibility: hidden;
                position: absolute;
                bottom: 100%;
                left: 50%;
                transform: translateX(-50%);
                margin-bottom: 10px;
                background: linear-gradient(135deg, #1a1d2e, #12141f);
                border: 1px solid #ff4655;
                border-radius: 16px;
                padding: 12px 20px;
                min-width: 180px;
                z-index: 100;
                opacity: 0;
                transition: all 0.3s ease;
                pointer-events: none;
                box-shadow: 0 5px 20px rgba(0,0,0,0.4);
            }

            .tier-badge:hover .tier-tooltip {
                visibility: visible;
                opacity: 1;
            }

            .tooltip-tier-name {
                font-weight: 700;
                font-size: 16px;
                margin-bottom: 8px;
                text-align: center;
            }

            .tooltip-points {
                font-size: 12px;
                color: #ff8c42;
                text-align: center;
            }

            .modal-close-btn {
                background: linear-gradient(135deg, #ff4655, #ff6b3d);
                border: none;
                padding: 12px 24px;
                border-radius: 40px;
                color: white;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                width: calc(100% - 40px);
                margin: 0 20px 30px 20px;
            }

            .modal-close-btn:hover {
                transform: scale(1.02);
                box-shadow: 0 5px 15px rgba(255, 70, 85, 0.4);
            }

            @media (max-width: 1100px) {
                .tiers-horizontal { flex-direction: column; }
                .tier-card { min-width: auto; }
                .modal-content { width: 90%; margin: 20% auto; }
                .header-content { flex-direction: column; text-align: center; }
                .servers-buttons { flex-direction: column; align-items: center; }
                .leaderboard-header, .leaderboard-row {
                    grid-template-columns: 60px 1fr 120px 120px 70px;
                    font-size: 11px;
                    padding: 12px 15px;
                }
            }
        </style>
        <script>
            let currentServer = 'netherop';
            let currentSection = 'tierlist';
            let tiersData = {};
            let leaderboardData = [];
            let searchTerm = '';

            // Очки для NetherOP
            const SUB_TIER_POINTS_NETHEROP = {
                "HT1": 10, "LT1": 8, "HT2": 7, "LT2": 6,
                "HT3": 5, "LT3": 4, "HT4": 3, "LT4": 2, "HT5": 1, "LT5": 1
            };

            // Очки для Beast
            const SUB_TIER_POINTS_BEAST = {
                "HT1": 10, "LT1": 8, "HT2": 7, "LT2": 6,
                "HT3": 5, "LT3": 4, "HT4": 3, "LT4": 2, "HT5": 1, "LT5": 1
            };

            function truncateName(name) {
                if (name.length > 10) return name.substring(0, 10) + '...';
                return name;
            }

            function toggleSection(section) {
                currentSection = section;
                document.getElementById('tierlist-section').classList.add('hidden');
                document.getElementById('leaderboard-section').classList.add('hidden');
                document.getElementById('queue-section').classList.add('hidden');

                document.getElementById(section + '-section').classList.remove('hidden');

                document.querySelectorAll('.nav-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                document.querySelector(`.nav-btn[data-section="${section}"]`).classList.add('active');

                const serverSelector = document.querySelector('.server-selector');
                if (section === 'tierlist') {
                    serverSelector.classList.remove('hidden');
                } else {
                    serverSelector.classList.add('hidden');
                }

                if (section === 'leaderboard') {
                    loadLeaderboard();
                }
            }

            function switchServer(server) {
                currentServer = server;
                document.querySelectorAll('.server-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                document.querySelector(`.server-btn.${server}`).classList.add('active');

                if (currentSection === 'tierlist') {
                    loadPlayers();
                }
            }

            async function loadPlayers() {
                try {
                    const response = await fetch(`/api/players/${currentServer}`);
                    tiersData = await response.json();

                    for (let tierNum = 1; tierNum <= 5; tierNum++) {
                        const players = tiersData[`Tier ${tierNum}`] || [];
                        const countSpan = document.getElementById(`tier${tierNum}-count`);
                        const playersList = document.getElementById(`tier${tierNum}-list`);

                        if (countSpan) countSpan.innerText = players.length;

                        if (playersList) {
                            if (players.length === 0) {
                                playersList.innerHTML = '<div class="empty-players"><i class="fas fa-users"></i> Нет игроков</div>';
                            } else {
                                playersList.innerHTML = players.map(p => {
                                    const safeUsername = p.username.replace(/\\\\/g, '\\\\\\\\').replace(/'/g, "\\\\'").replace(/"/g, '&quot;');
                                    return `
                                        <div class="player-item" onclick="openModal('${safeUsername}')">
                                            <span class="player-name">${truncateName(p.username)}</span>
                                            <span class="player-subtier">${p.sub_tier}</span>
                                        </div>
                                    `;
                                }).join('');
                            }
                        }
                    }

                    if (searchTerm) filterPlayers();
                } catch (error) {
                    console.error('Ошибка загрузки:', error);
                }
            }

            function filterPlayers() {
                const searchInput = document.getElementById('globalSearch');
                searchTerm = searchInput ? searchInput.value.toLowerCase() : '';

                for (let tierNum = 1; tierNum <= 5; tierNum++) {
                    const players = tiersData[`Tier ${tierNum}`] || [];
                    const filteredPlayers = players.filter(p => p.username.toLowerCase().includes(searchTerm));
                    const playersList = document.getElementById(`tier${tierNum}-list`);
                    const countSpan = document.getElementById(`tier${tierNum}-count`);

                    if (countSpan) countSpan.innerText = filteredPlayers.length;

                    if (playersList) {
                        if (filteredPlayers.length === 0) {
                            playersList.innerHTML = '<div class="empty-players"><i class="fas fa-search"></i> Игроков не найдено</div>';
                        } else {
                            playersList.innerHTML = filteredPlayers.map(p => {
                                const safeUsername = p.username.replace(/\\\\/g, '\\\\\\\\').replace(/'/g, "\\\\'").replace(/"/g, '&quot;');
                                return `
                                    <div class="player-item" onclick="openModal('${safeUsername}')">
                                        <span class="player-name">${truncateName(p.username)}</span>
                                        <span class="player-subtier">${p.sub_tier}</span>
                                    </div>
                                `;
                            }).join('');
                        }
                    }
                }
            }

            async function loadLeaderboard() {
                try {
                    const response = await fetch(`/api/leaderboard/all`);
                    leaderboardData = await response.json();
                    const container = document.getElementById('leaderboard-list');

                    if (!container) return;

                    if (leaderboardData.length === 0) {
                        container.innerHTML = '<div class="empty-players" style="padding: 50px;"><i class="fas fa-trophy"></i> Нет данных для лидерборда</div>';
                        return;
                    }

                    container.innerHTML = leaderboardData.map((player, index) => {
                        let rankClass = '';
                        if (index === 0) rankClass = 'rank-1';
                        else if (index === 1) rankClass = 'rank-2';
                        else if (index === 2) rankClass = 'rank-3';

                        const opTierHtml = player.op_tier 
                            ? `<span class="tier-value op">${player.op_tier}</span>`
                            : `<span class="tier-empty">—</span>`;

                        const beastTierHtml = player.beast_tier 
                            ? `<span class="tier-value beast">${player.beast_tier}</span>`
                            : `<span class="tier-empty">—</span>`;

                        return `
                            <div class="leaderboard-row">
                                <div class="rank ${rankClass}">#${player.rank}</div>
                                <div class="player-name-leaderboard">${player.username}</div>
                                <div class="tier-column">
                                    <div class="tier-server-name op">NetherOP</div>
                                    ${opTierHtml}
                                </div>
                                <div class="tier-column">
                                    <div class="tier-server-name beast">Beast</div>
                                    ${beastTierHtml}
                                </div>
                                <div class="player-points">${player.total_points}</div>
                            </div>
                        `;
                    }).join('');
                } catch (error) {
                    console.error('Ошибка загрузки лидерборда:', error);
                }
            }

            function openModal(username) {
                const player = leaderboardData.find(p => p.username === username);
                if (!player) return;

                const modal = document.getElementById('playerModal');
                const modalPlayerName = document.getElementById('modalPlayerName');
                const modalPosition = document.getElementById('modalPosition');
                const modalOverallPoints = document.getElementById('modalOverallPoints');
                const modalTiersContainer = document.getElementById('modalTiersContainer');

                const opPoints = SUB_TIER_POINTS_NETHEROP[player.op_tier] || 0;
                const beastPoints = SUB_TIER_POINTS_BEAST[player.beast_tier] || 0;

                modalPlayerName.textContent = player.username;
                modalPosition.textContent = player.rank;
                modalOverallPoints.textContent = player.total_points;

                modalTiersContainer.innerHTML = `
                    <div class="tier-badge op">
                        OP ${player.op_tier || '—'}
                        <div class="tier-tooltip">
                            <div class="tooltip-tier-name">NetherOP</div>
                            <div class="tooltip-points">🎯 ${opPoints} очков</div>
                        </div>
                    </div>
                    <div class="tier-badge beast">
                        Beast ${player.beast_tier || '—'}
                        <div class="tier-tooltip">
                            <div class="tooltip-tier-name">Beast</div>
                            <div class="tooltip-points">🎯 ${beastPoints} очков</div>
                        </div>
                    </div>
                `;

                modal.style.display = 'block';
            }

            function closeModal() {
                document.getElementById('playerModal').style.display = 'none';
            }

            function toggleDiscordDropdown() {
                const dropdown = document.getElementById('discordDropdown');
                dropdown.classList.toggle('show');
            }

            function openDiscordServer(server) {
                if (server === 'netherop') {
                    window.open('https://discord.gg/ZBkNqH8gRx', '_blank');
                } else if (server === 'beast') {
                    window.open('https://discord.gg/EkjzxqJuCE', '_blank');  // ← ЗАМЕНИТЕ НА ССЫЛКУ BEAST
                }
                document.getElementById('discordDropdown').classList.remove('show');
            }

            document.addEventListener('click', function(event) {
                const dropdown = document.getElementById('discordDropdown');
                const btn = document.querySelector('.discord-main-btn');
                if (dropdown && btn && !btn.contains(event.target) && !dropdown.contains(event.target)) {
                    dropdown.classList.remove('show');
                }
            });

            window.onclick = function(event) {
                const modal = document.getElementById('playerModal');
                if (event.target === modal) modal.style.display = 'none';
            }

            setInterval(() => {
                if (currentSection === 'tierlist') loadPlayers();
                if (currentSection === 'leaderboard') loadLeaderboard();
            }, 5000);

            loadPlayers();
            loadLeaderboard();
        </script>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="logo">ARENA<span>TIERS</span></div>
                <div class="nav">
                    <button class="nav-btn active" data-section="tierlist" onclick="toggleSection('tierlist')">Tier List</button>
                    <button class="nav-btn" data-section="queue" onclick="toggleSection('queue')">Queue</button>
                    <button class="nav-btn" data-section="leaderboard" onclick="toggleSection('leaderboard')">Leaderboard</button>
                </div>
                <div class="server-selector">
                    <button class="server-btn netherop active" onclick="switchServer('netherop')">NetherOP</button>
                    <button class="server-btn beast" onclick="switchServer('beast')">Beast</button>
                </div>
                <div class="search-container">
                    <i class="fas fa-search search-icon"></i>
                    <input type="text" class="search-input" id="globalSearch" placeholder="Search players..." onkeyup="filterPlayers()">
                </div>
                <div class="discord-dropdown">
                    <button class="discord-main-btn" onclick="toggleDiscordDropdown()">
                        <i class="fab fa-discord"></i> Discord
                    </button>
                    <div class="discord-dropdown-content" id="discordDropdown">
                        <div class="discord-server-item" onclick="openDiscordServer('netherop')">
                            <i class="fab fa-discord"></i> NetherOP
                        </div>
                        <div class="discord-server-item" onclick="openDiscordServer('beast')">
                            <i class="fab fa-discord"></i> Beast
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="main-content">
            <div id="tierlist-section" class="section">
                <div class="section-header">
                    <div class="section-title">TIER LIST</div>
                </div>
                <div class="tiers-horizontal">
                    <div class="tier-card tier-1"><div class="tier-card-header"><span class="tier-card-name">🥇 Tier 1</span><span class="tier-card-count" id="tier1-count">0</span></div><div class="tier-players-list"><div class="players-list-vertical" id="tier1-list"></div></div></div>
                    <div class="tier-card tier-2"><div class="tier-card-header"><span class="tier-card-name">🥈 Tier 2</span><span class="tier-card-count" id="tier2-count">0</span></div><div class="tier-players-list"><div class="players-list-vertical" id="tier2-list"></div></div></div>
                    <div class="tier-card tier-3"><div class="tier-card-header"><span class="tier-card-name">🥉 Tier 3</span><span class="tier-card-count" id="tier3-count">0</span></div><div class="tier-players-list"><div class="players-list-vertical" id="tier3-list"></div></div></div>
                    <div class="tier-card tier-4"><div class="tier-card-header"><span class="tier-card-name">🏅 Tier 4</span><span class="tier-card-count" id="tier4-count">0</span></div><div class="tier-players-list"><div class="players-list-vertical" id="tier4-list"></div></div></div>
                    <div class="tier-card tier-5"><div class="tier-card-header"><span class="tier-card-name">🏅 Tier 5</span><span class="tier-card-count" id="tier5-count">0</span></div><div class="tier-players-list"><div class="players-list-vertical" id="tier5-list"></div></div></div>
                </div>
            </div>

            <div id="leaderboard-section" class="section hidden">
                <div class="section-header">
                    <div class="section-title">LEADERBOARD</div>
                </div>
                <div class="leaderboard-table">
                    <div class="leaderboard-header">
                        <div>RANK</div>
                        <div>PLAYER</div>
                        <div>NETHEROP</div>
                        <div>BEAST</div>
                        <div>POINTS</div>
                    </div>
                    <div id="leaderboard-list"><div class="loader"><i class="fas fa-spinner"></i> Loading...</div></div>
                </div>
            </div>

            <div id="queue-section" class="section hidden">
                <div class="section-header">
                    <div class="section-title">QUEUE</div>
                </div>
                <div class="queue-container">
                    <div class="queue-section">
                        <div class="queue-title"><i class="fas fa-clipboard-list"></i> Вайтлист</div>
                        <div class="queue-text">Вам необходимо авторизоваться в Вайтлисте и получить роль Whitelist. Для того чтобы авторизоваться зайдите в канал Тестирование. После перехода в канал тестирования нажмите на кнопку Пройти тест, а затем заполните поля. После авторизации у вас появится доступ к каналу Очередь.</div>
                        <div class="cd-badge"><i class="fas fa-hourglass-half"></i> КД на тесты - 21 день</div>
                        <div class="license-note"><i class="fas fa-gamepad"></i> сервера без лицензии</div>
                    </div>

                    <div class="queue-section">
                        <div class="queue-title"><i class="fas fa-clock"></i> Очередь</div>
                        <div class="queue-text">Вам необходимо дождаться пока кто-то из тестеров откроет очередь. После открытия очереди вы будете упомянуты в канале и сможете войти в неё. Для входа в очередь необходимо нажать на кнопку Войти.</div>

                        <div class="active-queue">
                            <div style="font-size: 20px; font-weight: bold; margin-bottom: 15px;">🔥 Очередь доступна!</div>
                            <div class="queue-text">Жми на кнопку Войти для входа в очередь.<br>Используй команду /Leave для выхода из очереди.</div>
                            <div style="margin: 20px 0;">
                                <div style="color: #ff4655; font-weight: bold; margin-bottom: 10px;">Очередь:</div>
                                <ul class="queue-list">
                                    <li>1. <span class="mention">@reflective</span></li>
                                    <li>2. <span class="mention">@angel</span></li>
                                    <li>3. <span class="mention">@akno214</span></li>
                                </ul>
                            </div>
                            <div style="margin: 20px 0;">
                                <div style="color: #ff4655; font-weight: bold; margin-bottom: 10px;">Активные тестеры:</div>
                                <ul class="queue-list">
                                    <li>1. <span class="mention">@crybabyangels1</span></li>
                                </ul>
                            </div>
                            <button class="btn-join" onclick="alert('Вы вошли в очередь!')"><i class="fas fa-sign-in-alt"></i> Войти</button>
                        </div>
                    </div>

                    <div class="queue-section">
                        <div class="queue-title"><i class="fas fa-gamepad"></i> Тестирование</div>
                        <div class="queue-text">После входа в очередь вам необходимо дождаться пока вы зайдёте 1-е место в очереди. После чего вам откроют тикет, в котором вы договоритесь с тестером и пройдёте тест.</div>
                    </div>

                    <div class="queue-section" style="text-align: center;">
                        <div class="queue-title" style="justify-content: center;"><i class="fab fa-discord"></i> Discord Сервера</div>
                        <div class="servers-buttons">
                            <div class="server-card netherop" onclick="window.open('https://discord.gg/ZBkNqH8gRx', '_blank')">
                                <div class="server-icon"><i class="fab fa-discord"></i></div>
                                <div class="server-name">NethOP</div>
                                <div class="server-desc">Незеритовая броня</div>
                            </div>
                            <div class="server-card beast" onclick="window.open('https://discord.gg/EkjzxqJuCE', '_blank')">
                                <!-- ↑↑↑ ЗАМЕНИТЕ НА ССЫЛКУ BEAST ↑↑↑ -->
                                <div class="server-icon"><i class="fab fa-discord"></i></div>
                                <div class="server-name">Beast</div>
                                <div class="server-desc">Алмазная броня</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div id="playerModal" class="modal">
            <div class="modal-content">
                <span class="close-modal" onclick="closeModal()">&times;</span>
                <div class="modal-player-name" id="modalPlayerName">_DanFace_YT_</div>
                <div class="modal-stats">
                    <div class="stat-item">
                        <div class="stat-label">ПОЗИЦИЯ</div>
                        <div class="stat-value" id="modalPosition">48</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">ОЧКИ</div>
                        <div class="stat-value" id="modalOverallPoints">32</div>
                    </div>
                </div>
                <div class="modal-tiers-section">
                    <div class="tiers-title">ТИРЫ</div>
                    <div class="tiers-grid" id="modalTiersContainer"></div>
                </div>
                <button class="modal-close-btn" onclick="closeModal()">Закрыть</button>
            </div>
        </div>
    </body>
    </html>
    """


@app.route("/how-to-pass")
def how_to_pass():
    return '<meta http-equiv="refresh" content="0;url=/"><script>window.location.href = "/";</script>'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
