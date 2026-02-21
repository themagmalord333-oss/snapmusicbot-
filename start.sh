#!/bin/bash
echo "🚀 Starting Instagram Bot..."

# Print environment info (without sensitive data)
echo "📊 Environment:"
echo "  - User: $INSTAGRAM_USERNAME"
echo "  - Target: $TARGET_USERNAME"
echo "  - Message count: $MESSAGE_COUNT"

# Run the bot
python bot.py --mode web

# Keep alive
tail -f bot.log