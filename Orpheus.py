#!/usr/bin/env python3
"""
Orpheus - YouTube → MP3 pentru Audi Concert 3
Citește link.txt → descarcă toate melodiile direct în /mnt/Pergamena/Muzica/
MP3 CBR 320kbps, fără subfoldere, gata de ars pe CD.
"""

import sys
import subprocess
import logging
from pathlib import Path

# ─────────────────────────── CONFIG ───────────────────────────
OUTPUT_ROOT = Path("/mnt/Pergamena/Muzica")
LINK_FILE   = Path("link.txt")

# ─────────────────────────── LOGGING ──────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("orpheus.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("Orpheus")


def check_deps() -> bool:
    ok = True
    for tool in ["yt-dlp", "ffmpeg"]:
        r = subprocess.run(["which", tool], capture_output=True)
        if r.returncode != 0:
            log.error(f"Lipsă: {tool}")
            if tool == "yt-dlp":
                log.error("  pip install yt-dlp --break-system-packages")
            else:
                log.error("  sudo apt install ffmpeg")
            ok = False
    return ok


def download(url: str) -> bool:
    url = url.strip()
    if not url or url.startswith("#"):
        return True

    log.info(f"⬇  {url}")

    # Toate melodiile merg direct în /mnt/Pergamena/Muzica/Titlu.mp3
    output_template = str(OUTPUT_ROOT / "%(title)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format",       "mp3",
        "--audio-quality",      "0",
        "--postprocessor-args", "ffmpeg:-b:a 320k -ar 44100",   # CBR 320k, 44.1kHz
        "--embed-thumbnail",                                      # cover în ID3
        "--embed-metadata",                                       # titlu/artist în ID3
        "--output",             output_template,
        "--yes-playlist",                                         # descarcă tot albumul/playlist-ul
        "--progress",
        "--no-warnings",
        "--ignore-errors",                                        # sare peste melodii blocate
        "--sleep-interval",     "1",
        "--no-overwrites",                                        # nu suprascrie existente
        url,
    ]

    result = subprocess.run(cmd, text=True)

    if result.returncode == 0:
        log.info(f"  ✓ Gata")
        return True
    else:
        log.error(f"  ✗ Eșuat: {url}")
        return False


def main():
    if not check_deps():
        sys.exit(1)

    if not LINK_FILE.exists():
        log.error(f"Nu găsesc {LINK_FILE}")
        log.info("Creează link.txt cu câte un URL YouTube pe linie.")
        sys.exit(1)

    links = [
        l.strip()
        for l in LINK_FILE.read_text(encoding="utf-8").splitlines()
        if l.strip() and not l.strip().startswith("#")
    ]

    if not links:
        log.warning("link.txt e gol.")
        sys.exit(0)

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    log.info(f"🎵 {len(links)} URL-uri → {OUTPUT_ROOT}")
    log.info("─" * 50)

    ok_n = fail_n = 0
    for url in links:
        ok      = download(url)
        ok_n   += ok
        fail_n += not ok

    mp3s = list(OUTPUT_ROOT.glob("*.mp3"))

    print(f"\n{'═'*50}")
    print(f"  🎵 ORPHEUS")
    print(f"{'═'*50}")
    print(f"  URL-uri:  ✓ {ok_n}  ✗ {fail_n}")
    print(f"  MP3-uri în folder: {len(mp3s)}")
    print(f"  📁 {OUTPUT_ROOT}")
    print(f"{'═'*50}")
    print(f"\n  Arde CD-ul cu:")
    print(f"  wodim -v speed=8 dev=/dev/cdrom -data {OUTPUT_ROOT}/*.mp3")
    print(f"{'═'*50}")


if __name__ == "__main__":
    main()
