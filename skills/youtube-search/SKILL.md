---
name: youtube-search
description: "Search YouTube for videos by keyword or list recent uploads from a channel handle"
license: MIT
allowed-tools: search_youtube run_bash
metadata:
  author: agent-forge
  version: "1.0.0"
  category: media
---

# YouTube Search

## Instructions

When the user asks about YouTube videos, channels, or uploads:

1. **Channel lookup** — If the user gives a handle (e.g., @zquad, zquad):
   - Use the `search_youtube` tool with `mode: "channel"` and the handle as the query
   - This lists the channel's most recent uploads

2. **Keyword search** — If the user asks to find videos on a topic:
   - Use the `search_youtube` tool with `mode: "search"` and the topic as the query

3. **Present results** clearly:
   - Show title, URL, upload date, duration, and view count
   - Format as a numbered list or table
   - Highlight the most recent or most relevant results

4. **Follow-up actions** — Offer to:
   - Search for more specific terms
   - Build a YouTube monitoring agent if they want automated tracking
   - Get details on a specific video

## Examples

- "Show me the latest videos from @zquad" → `search_youtube(query="@zquad", mode="channel")`
- "Find YouTube videos about AI agents" → `search_youtube(query="AI agents", mode="search")`
- "Search for gitagent tutorials" → `search_youtube(query="gitagent tutorials", mode="search")`
