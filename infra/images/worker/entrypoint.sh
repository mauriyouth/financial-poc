#!/bin/bash
set -e

# Start Worker
echo "🚀 Starting RQ worker..."
exec python worker.py
