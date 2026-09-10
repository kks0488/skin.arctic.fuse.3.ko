# Personal Kodi skin maintenance

This repository contains distributable skin source only. In the owner's workspace, operational instructions, session logs and private backups live in the sibling ../kodi-debug directory. Read ../kodi-debug/AGENTS.md and docs/CURRENT-STATE.md before TV work. Record each session's changes and verification in ../kodi-debug/docs/YYYY-MM-DD.md and refresh CURRENT-STATE.md.

Never commit userdata, account credentials, downloaded subtitles, personal Apple font binaries or runtime backups. Preserve the optional Apple SD Gothic Neo fontset and its external media/Fonts paths. Preserve the Korean local-library design and genre-specific browse labels. Run tools/build.py and use tools/safe_update.py for TV deployments after checking playback is stopped. Do not describe future Kodi compatibility or visual/playback results as verified without evidence.
