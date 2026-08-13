#!/usr/bin/env python3
"""Worker daemon for AutoClip Local processing jobs."""

import asyncio
import logging
import signal
import sys
from pathlib import Path

from app.core.config import get_settings
from app.jobs.orchestrator import run_worker_loop

# Ensure backend directory is in path for imports
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


def main() -> None:
    """Main entry point for the worker daemon."""
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger("worker_daemon")
    logger.info("Starting AutoClip Local worker daemon")
    logger.info("Poll interval: %.1fs", settings.worker_poll_interval)

    stop_event = asyncio.Event()

    def handle_signal(signum: int, frame: object) -> None:
        logger.info("Received signal %s, shutting down...", signum)
        stop_event.set()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        asyncio.run(run_worker_loop(stop_event))
    except KeyboardInterrupt:
        logger.info("Worker daemon stopped by user")
    except Exception as exc:
        logger.error("Worker daemon crashed: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
