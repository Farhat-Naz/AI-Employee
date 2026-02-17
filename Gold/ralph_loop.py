"""
ralph_loop.py — Gold Tier Core Engine
---------------------------------------
PLAN → ACT → OBSERVE → REFLECT → repeat

Multi-step task ko autonomously execute karta hai.
Har iteration audit log mein jaata hai.
Max iterations ke baad NEEDS_HUMAN mark karta hai.

Usage:
    python Gold/ralph_loop.py Gold/Needs_Action/TASK-001.md

Task file format:
    ## Steps
    - Step 1: description
    - Step 2: description
    ...
"""

import os
import re
import sys
import shutil
import time
from datetime import datetime

# Audit logger import (same folder)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_logger import AuditLogger

# ── Config ────────────────────────────────────────────────────────────────────

BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
NEEDS_ACTION_DIR = os.path.join(BASE_DIR, "Needs_Action")
DONE_DIR         = os.path.join(BASE_DIR, "Done")
FAILED_DIR       = os.path.join(BASE_DIR, "Failed")
MEMORY_DIR       = os.path.join(BASE_DIR, "Memory")

MAX_ITERATIONS   = 10
SKILL_NAME       = "RalphWiggumLoop"


# ── Step Parser ───────────────────────────────────────────────────────────────

def parse_steps(content: str) -> list[str]:
    """
    Extract steps from task file.
    Looks for a '## Steps' section and collects list items.
    """
    steps = []
    in_steps = False

    for line in content.splitlines():
        if re.match(r"^##\s+Steps", line, re.IGNORECASE):
            in_steps = True
            continue
        if in_steps:
            if line.startswith("## "):
                break  # next section — stop
            match = re.match(r"^\s*[-*]\s+(?:Step\s*\d+:\s*)?(.+)", line)
            if match:
                steps.append(match.group(1).strip())

    return steps


def parse_task_id(filepath: str) -> str:
    """Extract task ID from filename."""
    return os.path.splitext(os.path.basename(filepath))[0]


# ── Ralph Wiggum Loop ─────────────────────────────────────────────────────────

class RalphWiggumLoop:

    def __init__(self, task_filepath: str):
        self.filepath  = task_filepath
        self.task_id   = parse_task_id(task_filepath)
        self.log       = AuditLogger()
        self.iteration = 0
        self.completed_steps: list[str] = []
        self.failed_steps:    list[str] = []

        os.makedirs(DONE_DIR,   exist_ok=True)
        os.makedirs(FAILED_DIR, exist_ok=True)
        os.makedirs(MEMORY_DIR, exist_ok=True)

    # ── Core Loop ─────────────────────────────────────────────────────────────

    def run(self) -> str:
        """
        Main loop. Returns 'success', 'needs_human', or 'max_iterations'.
        """
        print(f"\n{'='*60}")
        print(f"[RALPH] Task: {self.task_id}")
        print(f"{'='*60}")

        # PLAN
        start = self.log.log_start(SKILL_NAME, "plan", self.task_id)
        steps = self._plan()
        self.log.log_end(SKILL_NAME, "plan", start, "success", self.task_id,
                         detail=f"{len(steps)} steps found")

        if not steps:
            self._handle_no_steps()
            return "needs_human"

        print(f"\n[PLAN] {len(steps)} steps:")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}")

        remaining = list(steps)

        # LOOP
        while remaining and self.iteration < MAX_ITERATIONS:
            self.iteration += 1
            step = remaining[0]

            print(f"\n[ITER {self.iteration}/{MAX_ITERATIONS}] ACT: {step}")

            # ACT
            act_start  = self.log.log_start(SKILL_NAME, f"act_step_{self.iteration}", self.task_id)
            act_result = self._act(step)
            self.log.log_end(SKILL_NAME, f"act_step_{self.iteration}", act_start,
                             act_result["status"], self.task_id, detail=step[:80])

            # OBSERVE
            obs_start = self.log.log_start(SKILL_NAME, f"observe_{self.iteration}", self.task_id)
            observation = self._observe(act_result)
            self.log.log_end(SKILL_NAME, f"observe_{self.iteration}", obs_start,
                             "success", self.task_id, detail=observation["summary"])

            # REFLECT
            ref_start  = self.log.log_start(SKILL_NAME, f"reflect_{self.iteration}", self.task_id)
            reflection = self._reflect(observation)
            self.log.log_end(SKILL_NAME, f"reflect_{self.iteration}", ref_start,
                             reflection["decision"], self.task_id)

            print(f"[REFLECT] Decision: {reflection['decision']} — {reflection['reason']}")

            if reflection["decision"] == "step_done":
                self.completed_steps.append(step)
                remaining.pop(0)

            elif reflection["decision"] == "retry":
                print(f"[RETRY] Retrying step: {step}")
                # Step stays at top of remaining

            elif reflection["decision"] == "needs_human":
                self._handle_blocked(step, reflection["reason"])
                return "needs_human"

        # Post-loop outcome
        if not remaining:
            self._handle_success(steps)
            return "success"
        else:
            self._handle_max_iterations(remaining)
            return "max_iterations"

    # ── PLAN ──────────────────────────────────────────────────────────────────

    def _plan(self) -> list[str]:
        with open(self.filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return parse_steps(content)

    # ── ACT ───────────────────────────────────────────────────────────────────

    def _act(self, step: str) -> dict:
        """
        Execute one step.
        Currently: simulates execution (marks step as done).
        Future: dispatch to MCP servers based on step keywords.
        """
        time.sleep(0.3)  # simulate work

        # Keyword-based routing (expandable)
        step_lower = step.lower()

        if any(kw in step_lower for kw in ["odoo", "invoice", "accounting"]):
            return {"status": "pending_integration", "output": "Odoo MCP not connected yet"}

        if any(kw in step_lower for kw in ["post", "tweet", "instagram", "facebook"]):
            return {"status": "pending_approval", "output": "Social media requires approval"}

        # Default: mark step as simulated-success
        return {"status": "success", "output": f"Step executed: {step}"}

    # ── OBSERVE ───────────────────────────────────────────────────────────────

    def _observe(self, act_result: dict) -> dict:
        status = act_result["status"]
        output = act_result.get("output", "")

        if status == "success":
            return {"summary": "Step completed successfully", "ok": True, "blocked": False}
        elif status == "pending_integration":
            return {"summary": f"Integration not ready: {output}", "ok": False, "blocked": True}
        elif status == "pending_approval":
            return {"summary": f"Approval needed: {output}", "ok": False, "blocked": True}
        else:
            return {"summary": f"Unknown status: {status}", "ok": False, "blocked": False}

    # ── REFLECT ───────────────────────────────────────────────────────────────

    def _reflect(self, observation: dict) -> dict:
        if observation["ok"]:
            return {"decision": "step_done", "reason": "Step succeeded"}
        elif observation["blocked"]:
            return {"decision": "needs_human", "reason": observation["summary"]}
        else:
            return {"decision": "retry", "reason": observation["summary"]}

    # ── Outcome Handlers ──────────────────────────────────────────────────────

    def _handle_success(self, steps: list[str]) -> None:
        print(f"\n[SUCCESS] All {len(steps)} steps completed!")
        self.log.log(SKILL_NAME, "task_complete", "success",
                     task_id=self.task_id,
                     detail=f"{len(steps)} steps in {self.iteration} iterations")

        # Move to Done/
        dest = os.path.join(DONE_DIR, os.path.basename(self.filepath))
        self._append_result_block("DONE", steps)
        shutil.move(self.filepath, dest)
        print(f"[MOVED] {self.task_id} -> Done/")

        # Memory append
        self._append_memory(f"SUCCESS — {self.task_id}: {len(steps)} steps completed")

    def _handle_blocked(self, blocked_step: str, reason: str) -> None:
        print(f"\n[NEEDS_HUMAN] Blocked on: {blocked_step}")
        print(f"[REASON] {reason}")
        self.log.log(SKILL_NAME, "needs_human", "BLOCKED",
                     task_id=self.task_id, detail=reason[:100])
        self._append_result_block("NEEDS_HUMAN", [], blocked_step, reason)
        self._append_memory(f"BLOCKED — {self.task_id}: {reason}")

    def _handle_no_steps(self) -> None:
        print(f"\n[WARNING] No steps found in task file: {self.task_id}")
        self.log.log(SKILL_NAME, "plan", "no_steps", task_id=self.task_id)
        self._append_memory(f"NO_STEPS — {self.task_id}: task file has no ## Steps section")

    def _handle_max_iterations(self, remaining: list[str]) -> None:
        print(f"\n[MAX_ITER] Reached {MAX_ITERATIONS} iterations. Remaining: {len(remaining)} steps")
        self.log.log(SKILL_NAME, "max_iterations", "BLOCKED",
                     task_id=self.task_id,
                     detail=f"{len(remaining)} steps remain after {MAX_ITERATIONS} iterations")
        dest = os.path.join(FAILED_DIR, os.path.basename(self.filepath))
        self._append_result_block("FAILED_MAX_ITER", self.completed_steps)
        shutil.move(self.filepath, dest)
        print(f"[MOVED] {self.task_id} -> Failed/")
        self._append_memory(f"MAX_ITER — {self.task_id}: {len(remaining)} steps incomplete")

    # ── File Helpers ──────────────────────────────────────────────────────────

    def _append_result_block(
        self,
        status:       str,
        done_steps:   list[str],
        blocked_step: str = "",
        reason:       str = ""
    ) -> None:
        """Append a result summary block to the task file."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            f"\n---\n",
            f"## Ralph Wiggum Loop Result\n",
            f"**Status:** {status}\n",
            f"**Completed At:** {ts}\n",
            f"**Iterations Used:** {self.iteration}\n",
        ]
        if done_steps:
            lines.append(f"**Steps Completed:**\n")
            for s in done_steps:
                lines.append(f"- [x] {s}\n")
        if blocked_step:
            lines.append(f"**Blocked On:** {blocked_step}\n")
            lines.append(f"**Reason:** {reason}\n")

        if os.path.exists(self.filepath):
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.writelines(lines)

    def _append_memory(self, entry: str) -> None:
        """Append lesson to Memory/decisions.md."""
        decisions_file = os.path.join(MEMORY_DIR, "decisions.md")
        ts = datetime.now().strftime("%Y-%m-%d")
        line = f"| {ts} | {self.task_id} | {entry} |\n"
        with open(decisions_file, "a", encoding="utf-8") as f:
            f.write(line)


# ── CLI Entry Point ───────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python ralph_loop.py <path_to_task_file>")
        print("Example: python Gold/ralph_loop.py Gold/Needs_Action/TASK-001.md")
        sys.exit(1)

    task_file = sys.argv[1]

    if not os.path.exists(task_file):
        print(f"[ERROR] Task file not found: {task_file}")
        sys.exit(1)

    loop   = RalphWiggumLoop(task_file)
    result = loop.run()

    print(f"\n[RALPH] Final result: {result.upper()}")


if __name__ == "__main__":
    main()
