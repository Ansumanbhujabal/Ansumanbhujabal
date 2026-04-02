# Profile README Redesign — Design Spec

## Goal

Replace the current "looking for entry level job" GitHub profile README with a clean, text-forward README that reads like a person wrote it — inspired by AbdelStark's approach. No widget slop. Pure markdown, confident voice, organized by what you're doing.

## Audience

Hiring managers at AI startups, potential collaborators, open source maintainers who see your issues/PRs.

## Design Principles

- **Text-first, no widgets** — no stat cards, no snake animations, no shields.io badges, no typing SVGs
- **Reads like a human** — not a dashboard or auto-generated profile
- **Confident, not desperate** — "here's what I build" not "please hire me"
- **Clean markdown tables** — project name + one-liner, nothing more
- **Sections by intent** — what you're building, what you're exploring, where you engage

## Structure

### 1. Opening Hook

One bold philosophical line. Sets tone immediately.

Example direction: Something about agents, autonomy, building systems that think — in your voice, not generic.

### 2. Narrative Bio

2-3 sentences max. Covers:
- Current role: AI Engineer at Anyfeast (stealth, London, remote)
- What you actually do: agentic systems, RAG pipelines, multi-agent architectures
- What you care about now: making AI agents production-ready

No bullet points. Just prose.

### 3. Currently Building

Markdown table. Two rows.

| Project | What it does |
|---------|-------------|
| [tribev2](link) | NeuroLens — interactive neuroscience analysis on Meta's TRIBE v2 brain encoding model. PyTorch, CLIP, Whisper. |
| [Moonsense](link) | Multi-agent AI skincare system — specialized agents for diagnosis, environment analysis, product matching, safety validation. |

### 4. Exploring

Markdown table. Two rows.

| Project | What it does |
|---------|-------------|
| [agentscope](link) | Alibaba's multi-agent framework. Digging into MCP, A2A protocol, production orchestration patterns. |
| [MiroFish](link) | Swarm intelligence engine — thousands of AI agents with independent personalities forecasting future scenarios. |

### 5. Open Source Engagement

Markdown table. Shows repos where you've filed issues, opened PRs, or participated in discussions. Just org/repo name + what it is. Links go to your specific issue/PR.

| Project | |
|---------|---|
| [LangGraph](link) | LangChain's agent orchestration framework |
| [CrewAI](link) | Multi-agent orchestration platform |
| [h2oGPT](link) | Open source LLM deployment |
| [Langflow](link) | Visual agent builder |
| [Ollama](link) | Local LLM runtime |
| [Agno](link) | Agent framework |
| [Browser Use](link) | Browser automation for AI agents |

### 6. Closing Thread

2-3 sentences connecting your work. Forward-looking. What's the thread through tribev2, Moonsense, MiroFish, agentscope? Something about agents becoming real, needing real engineering, and you being the person building that bridge.

### 7. Stats Dashboard

Keep the existing stats section — streaks, GitHub stats, language breakdown, activity graph. Use dark themes (tokyonight/algolia/prussian) to match the text-forward tone. Centered layout.

Includes:
- GitHub streak stats (prussian theme)
- Profile summary cards (stats, most-commit-language, repos-per-language, productive-time, profile-details)
- Activity graph (github-compact theme)

### 8. Footer

Centered, minimal:

```
LinkedIn · Medium · Resume
```

Using `<p align="center">` with `<a>` tags, separated by ` · `.

## What's Removed from Current README

- "Looking for an entry level job" headline
- Profile views counter
- Trophy widget
- "Please help" language
- Generic tech stack icons (Bootstrap, Sass, Express, etc.)
- ~~Streak stats, GitHub stats cards, activity graph~~ (KEEPING these)
- DagsHub link
- Redundant social links section
- Bottom wave SVG

## What's New

- Confident opening hook
- Narrative bio with current role
- Two-tier project showcase (building vs exploring)
- Clean OSS engagement table
- Philosophical closing that ties work together

## Constraints

- Pure GitHub-flavored Markdown + minimal inline HTML (only `align`, `href`, `src`)
- No `<style>` tags, no CSS classes, no JavaScript
- Must render correctly on GitHub's markdown renderer
- Links must be real and working
