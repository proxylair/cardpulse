from urllib.parse import quote_plus

CAMPID = "5339192526"

def ebay_link(term):
    q = quote_plus(term)
    return f"https://www.ebay.com/sch/i.html?_nkw={q}&mkevt=1&mkcid=1&mkrid=711-53200-19255-0&campid={CAMPID}&toolid=10001"

files = {
    "content/articles/2026-08-standard-budget-staples.md": "magic the gathering standard singles",
    "content/articles/2026-08-onepiece-starter-decks-31-36.md": "one piece card game starter deck",
    "content/articles/2026-08-pokemon-mega-evolution-budget.md": "pokemon mega evolution cards",
    "content/articles/2026-08-lorcana-attack-of-the-vine-chase-cards.md": "lorcana attack of the vine",
    "content/articles/2026-08-riftbound-vendetta-market-check.md": "riftbound vendetta tcg",
}

for fname, term in files.items():
    link = ebay_link(term)
    text = open(fname, encoding="utf-8").read()
    new_text = text.replace(
        "[Check current listings on eBay](#)",
        f"[Check current listings on eBay]({link})"
    )
    new_text = new_text.replace(
        "*(Affiliate links pending -- see the [about page](../about.html) once TCGplayer and eBay Partner Network applications are approved.)*",
        "*(TCGplayer link pending approval -- see the [about page](../about.html).)*"
    )
    if new_text == text:
        print(f"WARNING: no change made in {fname} (already updated?)")
    open(fname, "w", encoding="utf-8").write(new_text)
    print(f"{fname}: updated")