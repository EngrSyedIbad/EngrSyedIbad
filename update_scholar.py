"""
Fetch Google Scholar profile data and write scholar.json for the portfolio site.

Run by the GitHub Action in update-scholar.yml (daily). Google Scholar has no
official API, so this uses the `scholarly` library. If Scholar blocks the request,
the script exits with an error WITHOUT touching the existing scholar.json, so the
site keeps showing the last good data (and falls back to OpenAlex if it gets stale).

Local run:
    pip install scholarly
    python update_scholar.py
"""
import json
import sys
from datetime import datetime, timezone

from scholarly import scholarly

SCHOLAR_ID = "9TFudOQAAAAJ"
OUT_FILE = "scholar.json"


def main() -> int:
    author = scholarly.search_author_id(SCHOLAR_ID)
    author = scholarly.fill(author, sections=["basics", "indices", "counts", "publications"])

    pubs = []
    for p in author.get("publications", []):
        bib = p.get("bib", {})
        title = bib.get("title")
        if not title:
            continue
        try:
            year = int(bib.get("pub_year")) if bib.get("pub_year") else None
        except ValueError:
            year = None
        pub_id = p.get("author_pub_id")
        url = (
            f"https://scholar.google.com/citations?view_op=view_citation&hl=en"
            f"&user={SCHOLAR_ID}&citation_for_view={pub_id}"
            if pub_id else ""
        )
        pubs.append({
            "title": title,
            "year": year,
            "venue": bib.get("citation", ""),
            "citations": p.get("num_citations", 0),
            "url": url,
        })

    if not pubs:
        print("No publications returned; keeping existing scholar.json", file=sys.stderr)
        return 1

    out = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "citations": author.get("citedby", 0),
        "h_index": author.get("hindex", 0),
        "i10_index": author.get("i10index", 0),
        "publications": pubs,
    }
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Wrote {OUT_FILE}: {out['citations']} citations, h={out['h_index']}, {len(pubs)} papers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
