#!/usr/bin/env python3
"""Fetch financial news from RSS feeds — prioritised by market relevance."""
import sys, re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTEXT = ROOT / "context"
CONTEXT.mkdir(exist_ok=True)

# Priority tiers — higher tiers fill first, ensuring market-moving news isn't buried
FEEDS_TIER1 = [  # Markets, energy, geopolitics — always included
    ("CNBC Top News", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"),
    ("Bloomberg", "https://feeds.bloomberg.com/markets/news.rss"),
    ("MarketWatch", "http://feeds.marketwatch.com/marketwatch/topstories/"),
    ("OilPrice", "https://oilprice.com/rss/main"),
    ("Zero Hedge", "https://feeds.feedburner.com/zerohedge/feed"),
    ("CNBC Economy", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258"),
    ("CNBC Energy", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19836768"),
]

FEEDS_TIER2 = [  # World news, geopolitics
    ("BBC World", "http://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("BBC Business", "http://feeds.bbci.co.uk/news/business/rss.xml"),
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("Fed Reserve", "https://www.federalreserve.gov/feeds/press_all.xml"),
]

FEEDS_TIER3 = [  # Regional, tech — fill remaining slots
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    ("SCMP", "https://www.scmp.com/rss/91/feed"),
    ("Nikkei Asia", "https://asia.nikkei.com/rss"),
    ("TechCrunch", "https://techcrunch.com/feed/"),
    ("ABC News AU", "https://www.abc.net.au/news/feed/2942460/rss.xml"),
    ("Economic Times", "https://economictimes.indiatimes.com/rssfeedstopstories.cms"),
]

# Keywords that boost an article to always-include
BOOST_KEYWORDS = re.compile(
    r"(iran|oil|crude|brent|wti|opec|strait.?of.?hormuz|tariff|sanctions|"
    r"fed(eral reserve)?|rate.?cut|rate.?hike|cpi|inflation|gdp|jobs.?report|nfp|"
    r"war|missile|strike|invasion|ceasefire|nuclear|nato|china|taiwan|"
    r"gold|silver|copper|commodity|recession|default|debt.?ceiling|"
    r"bitcoin|crypto|ethereum|vix|volatility|crash|rally|bear.?market|bull.?market)",
    re.IGNORECASE
)

def fetch_feed(name, url):
    import feedparser
    articles = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:8]:
            title = entry.get("title", "").strip()
            summary = entry.get("summary", entry.get("description", "")).strip()
            summary = re.sub(r"<[^>]+>", "", summary)
            if len(summary) > 250:
                summary = summary[:250] + "..."
            published = entry.get("published", entry.get("updated", ""))
            if title:
                boosted = bool(BOOST_KEYWORDS.search(title + " " + summary))
                articles.append({
                    "source": name,
                    "title": title,
                    "summary": summary,
                    "published": published,
                    "boosted": boosted
                })
    except Exception as e:
        print("[feed-news] {}: {}".format(name, e), file=sys.stderr)
    return articles

def fetch_news():
    all_articles = []
    for feeds in [FEEDS_TIER1, FEEDS_TIER2, FEEDS_TIER3]:
        for name, url in feeds:
            all_articles.extend(fetch_feed(name, url))
    return all_articles

def write_output(articles):
    now = datetime.now().strftime("%Y-%m-%d %H:%M EST")

    seen_titles = set()
    boosted = []
    normal = []
    for a in articles:
        title_lower = a["title"].lower()
        if title_lower in seen_titles:
            continue
        seen_titles.add(title_lower)
        if a["boosted"]:
            boosted.append(a)
        else:
            normal.append(a)

    # Boosted articles first (always included), then normal up to 50 total
    ordered = boosted + normal
    lines = ["# Financial News — {}".format(now)]
    if boosted:
        lines.append("\n## Market-Moving\n")
        for a in boosted[:25]:
            lines.append("### {}".format(a["title"]))
            lines.append("*{}* — {}".format(a["source"], a["published"]))
            if a["summary"]:
                lines.append(a["summary"])
            lines.append("")

    lines.append("\n## General\n")
    count = len(boosted[:25])
    for a in normal:
        if count >= 50:
            break
        lines.append("### {}".format(a["title"]))
        lines.append("*{}* — {}".format(a["source"], a["published"]))
        if a["summary"]:
            lines.append(a["summary"])
        lines.append("")
        count += 1

    output = "\n".join(lines) + "\n"
    (CONTEXT / "news.md").write_text(output)
    print("[feed-news] {} articles written ({} boosted, {} general)".format(
        count, len(boosted[:25]), count - len(boosted[:25])))

if __name__ == "__main__":
    try:
        articles = fetch_news()
        if articles:
            write_output(articles)
        else:
            print("[feed-news] No articles, keeping cached", file=sys.stderr)
    except Exception as e:
        print("[feed-news] Error: {}".format(e), file=sys.stderr)
