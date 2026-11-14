# KAXMOK Separate 24/7 YouTube Live

This repository is independent from `kax1234/live-test`.

## Media folders
- Put MP4 backgrounds in `assets/backgrounds/`.
- Put MP3 tracks in `assets/music/`.
- The stream uses the first available background and rotates through the music files in a repeating playlist.

## GitHub Actions secrets
In **Settings → Secrets and variables → Actions**, add:
- `YT_STREAM_KEY`: stream key for https://youtube.com/live/XVF4AhsrUqM
- `ANALYTICS_INGEST_TOKEN`: must be the exact same value as the Cloudflare Worker secret `INGEST_TOKEN`.

Never commit or share either secret.

## Analytics
The chat reader connects to the live event ID `XVF4AhsrUqM` and sends viewer metadata to:
`POST https://kaxmok-analytics.kaxxmok.workers.dev/api/ingest`

It sends author ID, display name, avatar URL, moderator flag, and an empty `text` field. Chat message contents are not forwarded. Analytics only starts producing data when the YouTube live chat is available and viewers send messages.

## Start
Open **Actions → KAXMOK Separate 24/7 Live → Run workflow**.

GitHub-hosted runners have a maximum job duration. This workflow runs for up to 350 minutes and uses a six-hour schedule to start a fresh session. Scheduled starts depend on GitHub Actions availability, so uninterrupted 24/7 broadcasting is not guaranteed.

Only stream media that you have permission to broadcast. Uploading a file to GitHub does not grant YouTube streaming rights.
