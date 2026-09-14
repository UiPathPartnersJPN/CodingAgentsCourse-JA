# CLAUDE.md — UiPath Coding Agents Workshop

Read automatically every Claude Code session in this repo. Apply all rules below.

This course reuses the authoring framework from the **Agentic Practice Workshop**
(https://github.com/uipath-practice/AgenticPracticeCourse). The `Master/` rules,
`.claude/commands/`, `hooks/`, and `scripts/` are copied from there via
`bootstrap-framework.sh`. The differences specific to THIS course are below.

---

## Project purpose

A GitHub Pages–hosted MkDocs site teaching technical clients & partners to build
UiPath **agents** (low-code, coded, conversational) and **Maestro** orchestrations
(BPMN, Case Management, Flow) using **coding agents + the `uip` CLI**. Audience is
technical and knows the UiPath platform but is new to AI / coding agents.

**Scope is deliberately narrow.** Out of scope (separate courses): UI Automation,
Testing Automation, Document Understanding / IXP. See `course-outline.md` (one level up).

---

## What is DIFFERENT from the base framework

### 1. Knowledge base (SSOT) — separate and private
- The validated knowledge base lives **outside this repo** at `../knowledge-base/`.
- It is the single source of truth for product facts; lessons are generated FROM it.
- **NEVER copy KB content into this repo or commit it.** It may contain internal
  material. `knowledge-base/` is gitignored here as a safety net.
- When generating a lesson, read the relevant `../knowledge-base/concepts/**` files
  for accurate, current product facts, then write the lesson into `docs/`.

### 2. Two lesson-generation paths (both valid)
- **Screenshot path** (unchanged from base framework): for Studio Web / browser UI
  steps where participants need click-by-click instructions. Use `/new-lesson` with
  screenshots → metadata → page.
- **CLI / KB path** (new): for terminal/`uip` CLI/code steps, generate from KB
  concept files + captured CLI transcripts/commands rather than screenshots.
- A single lesson may mix both (e.g., CLI setup + a Studio Web screenshot).

### 3. Environment is configurable (not hardcoded)
- `main.py` (mkdocs-macros) provides `{{ training_url }}`, `{{ training_tenant }}`,
  `{{ env_label }}`, switched by the `COURSE_ENV` variable (`staging` | `prod`).
- **Always use these variables in the training-environment callout** — never hardcode
  a URL or tenant. Values:
  - staging: staging.uipath.com/partnersuccess, tenant `Workshops` (authoring)
  - prod: cloud.uipath.com/tpenlabs, tenant `CodingAgentsPractice` (release)
- Author/preview with `COURSE_ENV=staging`; CI deploys with `COURSE_ENV=prod`.

---

## Master reference files (copied from base framework)

Read the relevant file before creating or reviewing content:

| File | Covers |
|------|--------|
| `Master/Filesystem.md` | Directory & naming conventions, image folders, Archive |
| `Master/CourseStructure.md` | Page types (Overview, Lesson, Summary) + templates |
| `Master/Formatting.md` | Images, two-column layouts, code blocks, admonitions |
| `Master/Language.md` | Voice, tone, word choices, platform names |
| `Master/HOWTO.md` | Create / generate / publish / review / remove workflows |

If `Master/` is empty, run `./bootstrap-framework.sh` first.

---

## Quick reference (always in context)

- **Voice:** second person, short sentences, conversational. Avoid "leverage",
  "utilize", "seamlessly", "In this section we will", "Please note that".
- **Platform names** bold on first use: **Agent Builder**, **Maestro**, **Studio Web**,
  **Orchestrator**, **Action Center**, **ServiceNow**, **Integration Service**.
  Coding-agent terms: **Claude Code**, the **`uip` CLI**, **UiPath skills**.
- **Code blocks:** always fenced with a language identifier (use `bash` for CLI).
- **Drafts** are not added to `mkdocs.yml` nav; use `mkdocs.local.yml` to preview,
  `/publish-exercise` to promote.
- **Never delete** explanatory content; rephrase. Archive, don't delete, retired pages.
- Run `COURSE_ENV=staging mkdocs build` to verify before committing.

---

## Local preview

```bash
pip install -r requirements.txt
COURSE_ENV=staging mkdocs serve -f mkdocs.local.yml   # author with WIP nav
COURSE_ENV=prod    mkdocs build                       # release-equivalent check
```
