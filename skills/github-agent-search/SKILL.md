---
name: github-agent-search
description: "Searches for existing gitagent repositories on GitHub that match a given task or capability"
license: MIT
allowed-tools: github-api
metadata:
  author: agent-forge
  version: "1.0.0"
  category: agent-management
---

# GitHub Agent Search

## Instructions

Before creating a new agent, ALWAYS search for existing ones first.

### Search Strategy

1. **Search GitHub** for repositories that match the task:
   - `gh search repos "<task keywords>" --json fullName,description,url`
   - `gh search repos "gitagent <domain>" --json fullName,description,url`
   - Search the user's own repos: `gh repo list --json name,description,url`

2. **Check for agent.yaml** — A real gitagent will have an `agent.yaml` at the root:
   - `gh api repos/{owner}/{repo}/contents/agent.yaml` to verify

3. **Evaluate fitness** — For each candidate:
   - Does its description match the task?
   - Does it have the right skills?
   - Is it actively maintained (recent commits)?
   - Can it be extended or forked rather than rebuilt?

4. **Present results** as a table:

| Agent | Description | Skills | Last Updated | URL |
|-------|-------------|--------|--------------|-----|
| ...   | ...         | ...    | ...          | ... |

5. **Recommend**:
   - If a strong match exists → suggest using or forking it
   - If a partial match exists → suggest extending it with new skills
   - If no match → proceed to create a new agent

## Output Format

Always present search results before recommending creation. Even if no results found, show that the search was performed.
