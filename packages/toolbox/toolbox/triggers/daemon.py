#!/usr/bin/env python3
"""Trigger daemon - runs scheduled triggers"""

from toolbox.triggers.scheduler import Scheduler
from toolbox.triggers.trigger_store import TriggerDB


def main():
    # Initialize database
    db = TriggerDB.from_url("sqlite:///triggers.db")

    # Create and run scheduler
    scheduler = Scheduler(db)
    print("Starting trigger daemon...")
    scheduler.run()


if __name__ == "__main__":
    main()
