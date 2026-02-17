# 🧠 Agent Skills (Bronze Tier)

**Implementation:** `Bronze/Skills/skills.py`
**Watcher:** `Bronze/Skills/watcher.py`
**Workflow:** `/Inbox → /Needs_Action → /Done`

---

## Skill 1: triage_item

**Purpose:** Analyze a new file in `/Inbox`, classify it, assign priority, move to `/Needs_Action`.

**Trigger:** New `.md` file appears in `/Inbox` (auto via watcher, or manual call)

**Input:** Path to file inside `/Inbox`

**Behavior:**
- Read file content
- Classify task type: `bug_fix` / `setup` / `report` / `research` / `general`
- Assign priority tag: `High` / `Medium` / `Low`
- Append `## Triage Metadata` block to file
- Move file to `/Needs_Action`
- Call `update_dashboard`
- Log action in Dashboard Activity Log

**Output:** Updated file in `/Needs_Action`, Dashboard updated

**Manual use:**
```
python skills.py triage "Bronze/Inbox/my-task.md"
```

---

## Skill 2: summarize_item

**Purpose:** Generate a 3–5 line AI summary and append it to any task file.

**Input:** File path (any folder)

**Behavior:**
- Read file content
- Generate structured summary (file name, category, key content, follow-up flag)
- Append `## AI Summary` section to file (only once — skipped if already present)

**Output:** Updated file with `## AI Summary` section appended

**Manual use:**
```
python skills.py summarize "Bronze/Needs_Action/my-task.md"
```

---

## Skill 3: complete_item

**Purpose:** Mark a task as done, move it to `/Done`, update Dashboard.

**Input:** Path to file inside `/Needs_Action`

**Behavior:**
- Append `## Completion` block with timestamp
- Move file to `/Done`
- Call `update_dashboard`
- Log action in Dashboard Activity Log

**Output:** File moved to `/Done`, Dashboard updated

**Manual use:**
```
python skills.py complete "Bronze/Needs_Action/my-task.md"
```

---

## Skill 4: update_dashboard

**Purpose:** Synchronize `Dashboard.md` with real vault state.

**Trigger:** Called automatically by `triage_item` and `complete_item`, or manually

**Behavior:**
- Count `.md` files in `/Inbox`, `/Needs_Action`, `/Done`
- Update `## Task Summary` table
- List top-5 priority tasks from `/Needs_Action` (sorted: High → Medium → Low)
- Update `## Top Priority Tasks` section

**Output:** `Dashboard.md` updated with live counts and task list

**Manual use:**
```
python skills.py dashboard
```

---

## Watcher (Auto-Trigger)

**File:** `Bronze/Skills/watcher.py`

Monitors `/Inbox` continuously using `watchdog`. When a new `.md` file is detected, it automatically calls `triage_item`.

**Start watcher:**
```
pip install watchdog
python watcher.py
```

---

## Workflow Rules

| Rule | Description |
|------|-------------|
| Inbox first | All new tasks must enter via `/Inbox` |
| Triage required | `triage_item` must run before any other skill |
| No skipping | Tasks cannot jump directly to `/Done` |
| No deleting | Files are moved, never deleted |
| Dashboard always synced | Every state change updates Dashboard.md |

---

## Priority Classification

| Priority | Triggered By |
|----------|-------------|
| High | Keywords: urgent, critical, asap, immediately |
| Medium | Task type: bug_fix or setup |
| Low | All other tasks |

---

## Task Type Classification

| Type | Keywords |
|------|----------|
| bug_fix | bug, error, crash, urgent, critical |
| setup | setup, install, configure, deploy |
| report | report, summary, review, audit |
| research | research, explore, investigate |
| general | (default — no keyword match) |
