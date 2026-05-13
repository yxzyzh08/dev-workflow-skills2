# DOGFOOD-<NNN>: <one-line title>

| Field | Value |
|-------|-------|
| **ID** | DOGFOOD-<NNN> |
| **Filed** | <YYYY-MM-DD> |
| **Severity** | blocking / high / medium / low |
| **Status** | open / investigating / fix-pending / fixed / wontfix / duplicate |
| **Discovered in** | <Claude Code 2.x / Codex CLI 0.128.0 / both / ...> |
| **Component** | <skill name / binary script / hook / template / docs / spec> |
| **Fixed in** | <commit hash / PR number / "—" if not yet fixed> |

## Description

What went wrong, in 1–3 sentences. Include the user-visible symptom, not just the internal cause.

## Reproduction steps

Numbered steps that reliably reproduce the issue. Include the exact directory layout / command / user input. If the issue is harness-specific, say which harness + version.

```
1. cd ~/projects/myapp (empty directory)
2. claude → "I want to manage this with dev-workflow"
3. ...
```

## Expected behavior

What the spec / docs say should happen.

## Actual behavior

What actually happened. Paste verbatim error output / stderr / agent dialogue if it helps.

```
<paste here>
```

## Root cause (if known)

A guess or confirmed root cause. Cite the specific file / line / commit if you've already triaged.

## Proposed fix

What needs to change in `dev-workflow-skills2`. Be specific:

- File path(s) to edit
- One-line summary of the change
- Any spec implication (does this require a design proposal review cycle, or is it a polish-class fix?)

## Workaround (if any)

What can the dogfooder do *right now* to keep moving without the fix?

## Notes

Anything else: related issues, screenshots, links to handoff docs, etc.
