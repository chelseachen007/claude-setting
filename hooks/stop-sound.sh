#!/usr/bin/env bash
# Stop hook - plays sound when Claude needs user input (optimized)
afplay /System/Library/Sounds/Ping.aiff &
cat > /dev/null
