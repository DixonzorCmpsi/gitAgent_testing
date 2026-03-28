---
name: gitagent-scaffold
description: "Generates valid gitagent file structures (agent.yaml, SOUL.md, RULES.md, skills) from a task description"
license: MIT
allowed-tools: gitagent-cli
metadata:
  author: agent-forge
  version: "1.0.0"
  category: agent-management
---

# gitagent Scaffold

## Instructions

Generate a complete, spec-compliant gitagent definition from a task description.

### Process

1. **Parse the task** — Extract:
   - Primary purpose (what the agent does)
   - Domain (code, ops, data, writing, etc.)
   - Required capabilities (what tools/APIs it needs)
   - Risk level (does it modify things? access sensitive data?)

2. **Generate agent.yaml**:
   ```yaml
   spec_version: "0.1.0"
   name: <kebab-case-name>
   version: 0.1.0
   description: <1-2 sentence description>
   model:
     preferred: openai/gpt-5.2
     constraints:
       temperature: <0.1-0.7 based on task creativity needs>
       max_tokens: <appropriate for output size>
   skills:
     - <list relevant skills>
   runtime:
     max_turns: <based on task complexity>
     timeout: <in seconds>
   ```

3. **Generate SOUL.md** — Write a focused identity:
   - Who the agent is (1 sentence)
   - Communication style (direct, verbose, technical, friendly)
   - Core values (accuracy, speed, thoroughness, etc.)
   - Domain expertise (specific to the task)

4. **Generate RULES.md** — Define boundaries:
   - Must-always rules (safety, quality)
   - Must-never rules (prevent scope creep, dangerous actions)
   - Output format constraints

5. **Generate skills** — For each capability:
   - Create `skills/<name>/SKILL.md` with frontmatter
   - Write clear instructions the agent will follow
   - Specify allowed-tools per skill

### Templates by Domain

**Code agents** — temperature 0.2, skills: code-review, testing, refactoring
**Ops agents** — temperature 0.1, skills: monitoring, deployment, incident-response
**Data agents** — temperature 0.3, skills: analysis, visualization, querying
**Writing agents** — temperature 0.6, skills: drafting, editing, summarizing

## Validation

After scaffolding, always validate with `gitagent validate` to ensure spec compliance.
