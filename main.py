#!/usr/bin/env python3
"""
TeamFinder Telegram Bot Entrypoint
"""
import sys
import os
import asyncio

# Ensure teamfinder module is on path
current_dir = os.path.dirname(os.path.abspath(__file__))
teamfinder_dir = os.path.join(current_dir, "teamfinder")
if teamfinder_dir not in sys.path:
    sys.path.insert(0, teamfinder_dir)

from main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
