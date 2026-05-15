# job-aggregator

Polls job board RSS feeds every 2 hours and sends matching DevOps/infrastructure postings to Discord.

## Sources

- RemoteOK (devops, sysadmin, linux categories)
- WeWorkRemotely (devops/sysadmin category)
- Jobicy (admin category)
- Himalayas (all remote jobs)

## Filters

- Title must match a DevOps keyword (devops, sysadmin, cloud engineer, site reliability, etc.)
- Title must not contain seniority words (senior, staff, principal, lead, manager, etc.)
- Description must not require more than 2 years of experience
- Excludes postings targeting specific regions (India, LATAM, UK only, etc.)

## Setup

```bash
pip install -r requirements.txt
```

Create `.env`:

```
DISCORD_WEBHOOK=your_webhook_url_here
```

Run:

```bash
set -a && . .env && set +a && python3 aggregator.py
```

## Cron (every 2 hours)

```
0 */2 * * * set -a && . /home/jean/scripts/job-aggregator/.env && set +a && python3 /home/jean/scripts/job-aggregator/aggregator.py >> /home/jean/scripts/job-aggregator/aggregator.log 2>&1
```

Seen job IDs are stored in `seen_jobs.json` to prevent duplicate alerts.
