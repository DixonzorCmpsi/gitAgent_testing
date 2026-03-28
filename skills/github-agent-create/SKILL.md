---
name: github-agent-create
description: "Creates a new gitagent repository on GitHub with proper structure, identity, and skills"
license: MIT
allowed-tools: github-api gitagent-cli
metadata:
  author: agent-forge
  version: "1.0.0"
  category: agent-management
---

# GitHub Agent Create

## Instructions

When the user describes a task that needs a new agent:

1. **Design the agent** — Determine:
   - A clear, kebab-case name (e.g., `pr-summarizer`, `log-analyzer`)
   - What skills the agent needs
   - What tools it requires
   - What model constraints make sense (temperature, max_tokens)
   - What rules/boundaries it should have

2. **Scaffold the gitagent structure** using these files:
   - `agent.yaml` — manifest with spec_version 0.1.0, name, version, description, model, skills, tools, runtime
   - `SOUL.md` — identity, communication style, values, domain expertise
   - `RULES.md` — must-always, must-never, output constraints
   - `skills/<skill-name>/SKILL.md` — any custom skills the agent needs

3. **Create the GitHub repository**:
   - Use `gh repo create <name> --public --description "<desc>" --clone`
   - Add all gitagent files
   - Commit with message: "Initialize <agent-name> gitagent"
   - Push to GitHub

4. **Validate** — Run `gitagent validate` to confirm the agent is spec-compliant

5. **Report back** — Provide the GitHub URL and a summary of the agent's capabilities

## Example agent.yaml

```yaml
spec_version: "0.1.0"
name: pr-summarizer
version: 0.1.0
description: Summarizes pull requests into concise daily digests
model:
  preferred: openai/gpt-5.2
  constraints:
    temperature: 0.2
    max_tokens: 4096
skills:
  - pr-analysis
runtime:
  max_turns: 10
  timeout: 60
```

## Output Format

After creating an agent, always output:
- Agent name and version
- GitHub repository URL
- List of skills and tools
- How to run it: `gitagent run` or `gitagent export --format <target>`
