import re

files_links = {
    "content/articles/2026-08-standard-budget-staples.md": "https://www.ebay.com/sch/i.html?_nkw=magic+the+gathering+standard+singles&mkcid=1&mkrid=711-53200-19255-0&toolid=20023&campid=5339192526&customid=mtg-budget-staples&siteid=0&mkevt=1",
    "content/articles/2026-08-onepiece-starter-decks-31-36.md": "https://www.ebay.com/sch/i.html?_nkw=one+piece+card+game+starter+deck&mkcid=1&mkrid=711-53200-19255-0&toolid=20023&campid=5339192526&customid=onepiece-starter-decks&siteid=0&mkevt=1",
    "content/articles/2026-08-pokemon-mega-evolution-budget.md": "https://www.ebay.com/sch/i.html?_nkw=pokemon+mega+evolution+cards&mkcid=1&mkrid=711-53200-19255-0&toolid=20023&campid=5339192526&customid=pokemon-mega-evolution&siteid=0&mkevt=1",
    "content/articles/2026-08-lorcana-attack-of-the-vine-chase-cards.md": "https://www.ebay.com/sch/i.html?_nkw=lorcana+attack+of+the+vine&mkcid=1&mkrid=711-53200-19255-0&toolid=20023&campid=5339192526&customid=lorcana-attack-of-the-vine&siteid=0&mkevt=1",
    "content/articles/2026-08-riftbound-vendetta-market-check.md": "https://www.ebay.com/sch/i.html?_nkw=riftbound+vendetta+tcg&mkcid=1&mkrid=711-53200-19255-0&toolid=20023&campid=5339192526&customid=riftbound-vendetta&siteid=0&mkevt=1",
}

for fname, new_link in files_links.items():
    text = open(fname, encoding="utf-8").read()
    new_text = re.sub(
        r"\[Check current listings on eBay\]\(https://www\.ebay\.com[^\)]*\)",
        f"[Check current listings on eBay]({new_link})",
        text
    )
    if new_text == text:
        print(f"WARNING: no change in {fname}")
    open(fname, "w", encoding="utf-8").write(new_text)
    print(f"{fname}: updated")