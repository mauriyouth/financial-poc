#!/bin/bash

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Icons
ICON_INFO="ℹ️"
ICON_SUCCESS="✅"
ICON_WARNING="⚠️"
ICON_ERROR="❌"

function log() {
    local LEVEL=$1
    local MESSAGE=$2
    local TIMESTAMP=$(date +"%H:%M:%S")

    case "$LEVEL" in
        "info")
            echo -e "${BLUE}${ICON_INFO} [INFO] [${TIMESTAMP}] ${MESSAGE}${NC}"
            ;;
        "success")
            echo -e "${GREEN}${ICON_SUCCESS} [SUCCESS] [${TIMESTAMP}] ${MESSAGE}${NC}"
            ;;
        "warning")
            echo -e "${YELLOW}${ICON_WARNING} [WARNING] [${TIMESTAMP}] ${MESSAGE}${NC}"
            ;;
        "error")
            echo -e "${RED}${ICON_ERROR} [ERROR] [${TIMESTAMP}] ${MESSAGE}${NC}"
            ;;
        *)
            echo -e "[${TIMESTAMP}] ${MESSAGE}"
            ;;
    esac
}
