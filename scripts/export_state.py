"""
export_state.py
---------------
Run the MonopolySimulator and export game state to public/game_state.json
after every turn. The HTML board polls this file to live-update.

Usage:
    python scripts/export_state.py

Requirements:
    pip install -r requirements.txt
    (MonopolySimulator must be installed or cloned alongside this project)
"""

import sys
import os
import json
import time
import random

# ── adjust this path to point at the cloned MonopolySimulator repo ──────────
MONOSIM_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'MonopolySimulator')
sys.path.insert(0, MONOSIM_PATH)

from monosim.player import Player
from monosim.board import (
    get_board, get_roads, get_properties,
    get_community_chest_cards, get_bank
)

# ── output file (served by Netlify / any static host) ───────────────────────
OUT_FILE = os.path.join(os.path.dirname(__file__), '..', 'public', 'game_state.json')

# ── HK food square names (maps board index → your custom label) ─────────────
# Edit these to match your Hongkopoly theme!
HK_NAMES = {
    0:  "GO",
    1:  "Pineapple Bun",
    2:  "Community Chest",
    3:  "Egg Waffle",
    4:  "Income Tax",
    5:  "MTR Station",
    6:  "Wonton Noodle",
    7:  "Chance",
    8:  "Char Siu Bao",
    9:  "Siu Mai",
    10: "Jail / Just Visiting",
    11: "Curry Fish Ball",
    12: "Electric Co.",
    13: "Lo Mai Gai",
    14: "Cheung Fun",
    15: "Star Ferry",
    16: "Dim Sum House",
    17: "Community Chest",
    18: "Ha Gow",
    19: "Turnip Cake",
    20: "Free Parking",
    21: "Milk Tea",
    22: "Chance",
    23: "Egg Tart",
    24: "Wife Cake",
    25: "Tram Station",
    26: "Mango Pudding",
    27: "Swiss Chicken Wings",
    28: "Water Works",
    29: "Pan-Fried Bun",
    30: "Go To Jail",
    31: "Roast Goose",
    32: "Clay Pot Rice",
    33: "Community Chest",
    34: "Typhoon Shelter Crab",
    35: "Kowloon Station",
    36: "Chance",
    37: "Crispy Pork Belly",
    38: "Super Tax",
    39: "Mayfair → The Peak",
}

# ── player token icons (emoji fallbacks — replace with your image URLs) ──────
PLAYER_ICONS = {
    "player1": "🧋",   # milk tea token
    "player2": "🥟",   # dumpling token
}

PLAYER_COLORS = {
    "player1": "#e63946",
    "player2": "#457b9d",
}


def build_state(players, board, turn, event_log):
    """Serialize current game state to a JSON-serializable dict."""
    player_states = []
    for p in players:
        player_states.append({
            "name":     p.name,
            "position": p.position,
            "cash":     p.cash,
            "has_lost": p.has_lost(),
            "icon":     PLAYER_ICONS.get(p.name, "🎲"),
            "color":    PLAYER_COLORS.get(p.name, "#333"),
            "in_jail":  p.jail,
        })

    # Ownership map: square_name → player_name
    owned = {}
    for road_name, road in get_roads().items():
        if road['belongs_to'] is not None:
            # board_num is the square index
            owned[road['board_num']] = road['belongs_to'].name

    return {
        "turn":        turn,
        "timestamp":   time.time(),
        "players":     player_states,
        "owned":       owned,
        "event_log":   event_log[-12:],   # last 12 events
        "board_names": HK_NAMES,
        "game_over":   any(p.has_lost() for p in players),
    }


def write_state(state):
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    tmp = OUT_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, OUT_FILE)   # atomic write so the browser never reads a partial file
    print(f"[turn {state['turn']}] State written → {OUT_FILE}")


def run_simulation(seed=42, max_turns=2000, turn_delay=0.5):
    """
    Run a full 2-player game and write state after every turn.
    turn_delay: seconds to wait between turns (so the browser can see updates)
    """
    random.seed(seed)
    event_log = []

    bank            = get_bank()
    list_board      = get_board()
    dict_roads      = get_roads()
    dict_properties = get_properties()
    dict_cc_cards   = get_community_chest_cards()
    cc_deck         = list(dict_cc_cards.keys())

    player1 = Player('player1', 1, bank, list_board, dict_roads, dict_properties, cc_deck)
    player2 = Player('player2', 2, bank, list_board, dict_roads, dict_properties, cc_deck)

    player1.meet_other_players([player2])
    player2.meet_other_players([player1])

    players = [player1, player2]

    # Write initial state
    write_state(build_state(players, list_board, 0, event_log))

    for turn in range(1, max_turns + 1):
        for player in players:
            pos_before = player.position
            try:
                player.play()
            except Exception as e:
                event_log.append(f"[T{turn}] Error: {e}")

            pos_after = player.position
            square_name = HK_NAMES.get(pos_after, list_board[pos_after]['name'])
            event_log.append(
                f"[T{turn}] {player.name} moved {pos_before}→{pos_after} ({square_name}) | 💰${player.cash}"
            )

        write_state(build_state(players, list_board, turn, event_log))

        if any(p.has_lost() for p in players):
            loser  = next(p for p in players if p.has_lost())
            winner = next(p for p in players if not p.has_lost())
            event_log.append(f"🏆 {winner.name} WINS! {loser.name} is bankrupt.")
            write_state(build_state(players, list_board, turn, event_log))
            print(f"Game over at turn {turn}. Winner: {winner.name}")
            break

        time.sleep(turn_delay)

    print("Simulation complete.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Hongkopoly simulator → JSON exporter")
    parser.add_argument("--seed",      type=int,   default=42,  help="Random seed")
    parser.add_argument("--max-turns", type=int,   default=2000, help="Max turns")
    parser.add_argument("--delay",     type=float, default=0.5,  help="Seconds between turns")
    args = parser.parse_args()

    run_simulation(seed=args.seed, max_turns=args.max_turns, turn_delay=args.delay)
