# KAXMOK Separate 24/7 YouTube Live

This repository is independent from `kax1234/live-test`.

## Media folders

- Put MP4 backgrounds in `assets/backgrounds/`.
- Put MP3 music tracks in `assets/music/`.
- The current workflow selects the first available background and rotates through the music files in a repeating playlist.

## Required secret

In **Settings → Secrets and variables → Actions**, add:

- `YT_STREAM_KEY`: the stream key for the separate YouTube Live event:
  https://youtube.com/live/XVF4AhsrUqM

Never commit or share the stream key.

## Start

Open **Actions → KAXMOK Separate 24/7 Live → Run workflow**.

GitHub-hosted runners have a maximum job duration. This workflow runs for up to 350 minutes and has a six-hour schedule to start a fresh session. Scheduled starts depend on GitHub Actions availability, so this is not a guaranteed uninterrupted 24/7 broadcast.

## Current scope

This initial version streams the MP4 background with the MP3 playlist. Chat commands and live background switching are not included in this initial streaming workflow yet.

Only stream music and video that you have permission to broadcast. Uploading a file to GitHub does not grant YouTube streaming rights.
