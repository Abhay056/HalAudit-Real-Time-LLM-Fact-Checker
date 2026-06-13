"""
HalAudit ARQ Worker Entry Point

Usage:
    python run_worker.py

Or with arq directly:
    arq app.queue.worker.WorkerSettings
"""

import logging
import asyncio
# pyrefly: ignore [missing-import]
from arq import run_worker
from app.queue.worker import WorkerSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

if __name__ == "__main__":
    run_worker(WorkerSettings)
