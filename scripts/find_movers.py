#!/usr/bin/env python3
"""
find_movers.py
----------------
Compares the two most recent snapshots in data/snapshots/ and prints the
biggest price gainers/losers, per game. Needs at least 2 snapshots (a week
or more apart) to say anything -- that accumulated history is the actual
moat here, since TCGCSV/TCGplayer don't expose a "biggest movers" feed
themselves.

Usage: python3 scripts/find_movers.py [min_pct_change] [game_key]
  game_key: mtg | pokemon | onepiece | lorcana | riftbound  (default: all)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAP_DIR = ROOT / "data" / "snapshots"


def load_snapshots():
    return sorted(SNAP_DIR.glob("*.json"))


def index_game(snapshot, game_key):
    idx = {}
    game = snapshot.get("games", {}).get(game_key, {})
    for c in game.get("cards", []):
        if c.get("market_price") is None:
            continue
        idx[(c["name"], c["set"])] = float(c["market_price"])
    return idx


def report_game(old, new, game_key, min_pct):
    label = new.get("games", {}).get(game_key, {}).get("label", game_key)
    old_idx = index_game(old, game_key)
    new_idx = index_game(new, game_key)

    moves = []
    for key, new_price in new_idx.items():
        old_price = old_idx.get(key)
        if not old_price:
            continue
        pct = (new_price - old_price) / old_price * 100
        if abs(pct) >= min_pct:
            moves.append((pct, key[0], key[1], old_price, new_price))
    moves.sort(reverse=True)

    if not moves:
        return
    print(f"\n=== {label} ===")
    gainers = [m for m in moves if m[0] > 0][:10]
    losers = [m for m in moves if m[0] < 0][-10:]
    if gainers:
        print("Gainers:")
        for pct, name, setname, old_p, new_p in gainers:
            print(f"  {name} ({setname}): ${old_p:.2f} -> ${new_p:.2f}  ({pct:+.1f}%)")
    if losers:
        print("Losers:")
        for pct, name, setname, old_p, new_p in losers:
            print(f"  {name} ({setname}): ${old_p:.2f} -> ${new_p:.2f}  ({pct:+.1f}%)")


def main():
    min_pct = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
    game_filter = sys.argv[2] if len(sys.argv) > 2 else None

    files = load_snapshots()
    if len(files) < 2:
        print("Need at least 2 snapshots to compare. Run fetch_snapshot.py again next week.")
        return

    old = json.loads(files[-2].read_text())
    new = json.loads(files[-1].read_text())
    print(f"Comparing {files[-2].name} -> {files[-1].name}")

    games = [game_filter] if game_filter else list(new.get("games", {}).keys())
    for g in games:
        report_game(old, new, g, min_pct)


if __name__ == "__main__":
    main()
