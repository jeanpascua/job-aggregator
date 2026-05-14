#!/usr/bin/env python3
"""Polls RemoteOK + WeWorkRemotely RSS feeds, sends new DevOps matches to Discord."""

import feedparser
import requests
import json
import os
import re
import hashlib
from pathlib import Path
from datetime import datetime, timezone

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]
SEEN_FILE = Path(__file__).parent / "seen_jobs.json"

KEYWORDS = [
    "devops", "dev ops", "sysadmin", "sys admin", "systems administrator",
    "infrastructure engineer", "cloud engineer", "site reliability", "sre",
    "platform engineer", "linux admin", "linux engineer", "platform administrator",
    "kubernetes engineer", "automation engineer",
]

EXCLUDE_TITLE = [
    "senior", "sr.", "staff", "principal", "director",
    "vp ", "vice president", "head of", "manager", "lead",
    "account executive", "sales representative",
]

EXP_PATTERN = re.compile(
    r"(\d+)\+?\s*years?\s*(of\s*)?(experience|exp)\b"
    r"|minimum\s*(\d+)\s*years?"
    r"|at\s*least\s*(\d+)\s*years?",
    re.IGNORECASE,
)
MAX_YEARS = 2

EXCLUDE_LOCATIONS = [
    "india", "inr ", "latam", "latin america", "brazil", "brasil",
    "argentina", "colombia", "mexico", "poland", "uk only", "europe only",
    "south korea", "korea", "japan", "australia only", "new zealand",
    "u.s. applicants only", "us applicants only", "usa applicants only",
    "american applicants only", "uk applicants only", "eu applicants only",
    "europe applicants only", "european applicants only",
    "must be located in the us", "must reside in the us",
    "us residents only", "u.s. residents only", "us citizens only",
]

FEEDS = [
    ("RemoteOK", "https://remoteok.com/remote-devops-jobs.rss"),
    ("RemoteOK", "https://remoteok.com/remote-sys-admin-jobs.rss"),
    ("RemoteOK", "https://remoteok.com/remote-linux-jobs.rss"),
    ("WeWorkRemotely", "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss"),
    ("JobBank", "https://www.jobbank.gc.ca/jobsearch/feed/jobSearchRSSfeed?fage=2&fcid=296118&term=devops&sort=D&rows=100"),
    ("JobBank", "https://www.jobbank.gc.ca/jobsearch/feed/jobSearchRSSfeed?fage=2&fcid=1445&fcid=3751&fcid=297553&term=systems+administrator&sort=D&rows=100"),
    ("JobBank", "https://www.jobbank.gc.ca/jobsearch/feed/jobSearchRSSfeed?dkw=linux&fage=2&fcid=249&fcid=1090&fcid=1445&fcid=1923&fcid=1973&fcid=12369&fcid=12511&fcid=17389&fcid=25772&fcid=26655&fcid=227133&fcid=296309&fcid=296873&fcid=297236&fcid=297274&fcid=297530&fcid=297553&fn21=00011&fn21=10010&fn21=10019&fn21=11109&fn21=11202&fn21=12102&fn21=13100&fn21=13101&fn21=14103&fn21=21223&fn21=22220&fn21=30010&fn21=40010&fn21=40020&fn21=40021&fn21=40030&fn21=50010&term=administrator&sort=D&rows=100"),
]


def load_seen():
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text()))
    return set()


def save_seen(seen):
    SEEN_FILE.write_text(json.dumps(list(seen)))


def job_id(entry):
    raw = entry.get("id") or entry.get("link", "")
    return hashlib.md5(raw.encode()).hexdigest()


def strip_html(text):
    return re.sub(r"<[^>]+>", " ", text).strip()


def too_experienced(text):
    for m in EXP_PATTERN.finditer(text):
        years = int(next(v for v in m.groups() if v is not None))
        if years > MAX_YEARS:
            return True
    return False


def wrong_location(title, desc):
    combined = f"{title} {desc}".lower()
    return any(loc in combined for loc in EXCLUDE_LOCATIONS)


def matches(entry):
    title = entry.get("title", "").lower()
    if any(ex in title for ex in EXCLUDE_TITLE):
        return False
    if not any(kw in title for kw in KEYWORDS):
        return False
    desc = strip_html(entry.get("summary", ""))
    if too_experienced(desc):
        return False
    if wrong_location(title, desc):
        return False
    return True


def send_discord(source, entry):
    title = entry.get("title", "Job Posting")
    link = entry.get("link", "")
    raw_summary = strip_html(entry.get("summary", ""))
    summary = " ".join(raw_summary.split())[:400]
    payload = {
        "embeds": [{
            "title": title[:256],
            "url": link,
            "description": summary,
            "footer": {"text": source},
            "color": 0x5865F2,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }]
    }
    requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)


def main():
    seen = load_seen()
    new_count = 0

    for source, url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                jid = job_id(entry)
                if jid in seen:
                    continue
                seen.add(jid)
                if matches(entry):
                    send_discord(source, entry)
                    new_count += 1
        except Exception as e:
            print(f"Error {url}: {e}")

    save_seen(seen)
    print(f"{datetime.now().isoformat()} — {new_count} new matches sent")


if __name__ == "__main__":
    main()
