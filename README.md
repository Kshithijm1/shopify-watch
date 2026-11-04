# shopify-watch

Checks Shopify's careers pages every 60 seconds from GitHub Actions and sends an urgent push to your phone (and optionally an email) when a new internship posting appears. It doesn't need your laptop.

## Setup

1. **Phone:** Install **ntfy** (App Store / Play Store). Subscribe to a topic with a hard-to-guess name, e.g. `kshithij-shopify-7f3k9`. Allow notifications. On iOS, also allow Critical/Time-Sensitive alerts so it can break through Focus.
2. **GitHub:** Create a new **public** repo (public = unlimited free Actions minutes; private would burn the 2,000-minute free tier in ~1.5 days). Upload these files, keeping the `.github/workflows/` folder path.
3. **Secrets:** Repo → Settings → Secrets and variables → Actions → New repository secret:
   - `NTFY_TOPIC` = your topic name
   - `ALERT_EMAIL` = your email (optional, backup channel)
4. **Start it:** Actions tab → enable workflows → `shopify-watch` → **Run workflow**. Within a minute you should get a "Shopify watcher running" push showing how many existing postings it found.

## Notes
- The topic name is stored as a secret, so it stays hidden even though the repo is public.
- GitHub disables scheduled workflows on public repos after 60 days with no commits. If that happens, re-enable it in the Actions tab or push any commit.
- To stop it: Actions → shopify-watch → ⋯ → Disable workflow.
