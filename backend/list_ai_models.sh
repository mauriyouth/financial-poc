#!/bin/bash

# Script to fetch available models from Anthropic and Google APIs
# Usage: ./list_ai_models.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load environment variables from .env if it exists
if [ -f .env ]; then
    echo -e "${BLUE}Loading environment variables from .env...${NC}"
    export $(grep -v '^#' .env | xargs)
fi

# Check if required tools are installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is required but not installed. Install with: brew install jq${NC}"
    exit 1
fi

echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}        AI Model Discovery Script${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}\n"

# ============================================================
# ANTHROPIC MODELS
# ============================================================
echo -e "${BLUE}Fetching Anthropic Models from API...${NC}"

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}Warning: ANTHROPIC_API_KEY not set. Skipping Anthropic.${NC}\n"
else
    echo -e "${GREEN}Querying: https://api.anthropic.com/v1/models${NC}"
    echo -e "─────────────────────────────────────────────────\n"
    
    # Fetch models from Anthropic API
    RESPONSE=$(curl -s \
        https://api.anthropic.com/v1/models \
        -H "x-api-key: $ANTHROPIC_API_KEY" \
        -H "anthropic-version: 2023-06-01" \
        2>/dev/null || echo '{"error": "failed"}')
    
    if echo "$RESPONSE" | jq -e '.error' > /dev/null 2>&1; then
        ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error.message // "Unknown error"')
        echo -e "${RED}Error fetching models from Anthropic API: $ERROR_MSG${NC}\n"
    elif echo "$RESPONSE" | jq -e '.data' > /dev/null 2>&1; then
        # Parse and display models
        echo "$RESPONSE" | jq -r '.data[] | 
            "│ " + (.id | ljust(42)) + " │ " + (.display_name // .id | ljust(30)) + " │ " + (if .type then .type else "N/A" end | ljust(15)) + " │"' | 
        awk 'BEGIN {
            print "┌────────────────────────────────────────────┬────────────────────────────────┬─────────────────┐"
            print "│ Model ID                                   │ Display Name                   │ Type            │"
            print "├────────────────────────────────────────────┼────────────────────────────────┼─────────────────┤"
        }
        {print}
        END {
            print "└────────────────────────────────────────────┴────────────────────────────────┴─────────────────┘"
        }'
        
        MODEL_COUNT=$(echo "$RESPONSE" | jq -r '.data | length')
        echo -e "\n${GREEN}✓ Found $MODEL_COUNT Anthropic models${NC}\n"
        
        # Show additional model details
        echo -e "${BLUE}Model Details:${NC}"
        echo "$RESPONSE" | jq -r '.data[] | "  • \(.id): max_tokens=\(.max_tokens // "N/A"), created=\(.created_at // "N/A")"'
        echo ""
    else
        echo -e "${YELLOW}⚠ Unexpected response format from Anthropic API${NC}"
        echo -e "${YELLOW}Response: $RESPONSE${NC}\n"
    fi
fi

# ============================================================
# GOOGLE GEMINI MODELS
# ============================================================
echo -e "${BLUE}Fetching Google Gemini Models from API...${NC}"

if [ -z "$GEMINI_API_KEY" ] && [ -z "$GOOGLE_API_KEY" ]; then
    echo -e "${YELLOW}Warning: GEMINI_API_KEY or GOOGLE_API_KEY not set. Skipping Google.${NC}\n"
else
    API_KEY="${GEMINI_API_KEY:-$GOOGLE_API_KEY}"
    
    echo -e "${GREEN}Querying: https://generativelanguage.googleapis.com/v1beta/models${NC}"
    echo -e "─────────────────────────────────────────────────\n"
    
    # Fetch models from Google API
    RESPONSE=$(curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=$API_KEY" 2>/dev/null || echo '{"error": "failed"}')
    
    if echo "$RESPONSE" | jq -e '.error' > /dev/null 2>&1; then
        ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error.message // "Unknown error"')
        echo -e "${RED}Error fetching models from Google API: $ERROR_MSG${NC}\n"
    elif echo "$RESPONSE" | jq -e '.models' > /dev/null 2>&1; then
        # Parse and display only generateContent-capable models
        echo "$RESPONSE" | jq -r '.models[] | 
            select(.supportedGenerationMethods[]? == "generateContent") |
            "│ " + (.name | split("/")[1] | ljust(42)) + " │ " + (.displayName // "N/A" | ljust(30)) + " │ " + (.version // "N/A" | ljust(15)) + " │"' | 
        awk 'BEGIN {
            print "┌────────────────────────────────────────────┬────────────────────────────────┬─────────────────┐"
            print "│ Model ID                                   │ Display Name                   │ Version         │"
            print "├────────────────────────────────────────────┼────────────────────────────────┼─────────────────┤"
        }
        {print}
        END {
            print "└────────────────────────────────────────────┴────────────────────────────────┴─────────────────┘"
        }'
        
        MODEL_COUNT=$(echo "$RESPONSE" | jq -r '[.models[] | select(.supportedGenerationMethods[]? == "generateContent")] | length')
        echo -e "\n${GREEN}✓ Found $MODEL_COUNT Google Gemini models${NC}\n"
        
        # Show additional model details
        echo -e "${BLUE}Model Details:${NC}"
        echo "$RESPONSE" | jq -r '.models[] | 
            select(.supportedGenerationMethods[]? == "generateContent") |
            "  • " + (.name | split("/")[1]) + ": input_limit=" + (.inputTokenLimit // 0 | tostring) + ", output_limit=" + (.outputTokenLimit // 0 | tostring)'
        echo ""
    else
        echo -e "${YELLOW}⚠ Unexpected response format from Google API${NC}"
        echo -e "${YELLOW}Response preview: $(echo $RESPONSE | head -c 200)${NC}\n"
    fi
fi

# ============================================================
# SUMMARY
# ============================================================
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Summary:${NC}"
echo -e "─────────────────────────────────────────────────"

if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo -e "${GREEN}✓${NC} Anthropic API key configured"
else
    echo -e "${YELLOW}⚠${NC} Anthropic API key missing"
fi

if [ -n "$GEMINI_API_KEY" ] || [ -n "$GOOGLE_API_KEY" ]; then
    echo -e "${GREEN}✓${NC} Google API key configured"
else
    echo -e "${YELLOW}⚠${NC} Google API key missing"
fi

echo -e "\n${BLUE}Tip: Set API keys in .env file or export them:${NC}"
echo -e "  export ANTHROPIC_API_KEY=\"your-key\""
echo -e "  export GEMINI_API_KEY=\"your-key\""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}\n"
