# Antigravity Discord Agent Skill

This skill file defines the standard operating procedure (SOP) for an AI agent handling remote tasks via the Discord bridge.

## How to use (For Users)
1. Ensure this file (`discord_agent_skill.md`) is at the root of your project.
2. The `watcher.py` script will automatically instruct the AI agent to read this file whenever a new task is received.

---

## Agent Instructions (For AI)

You are operating via a headless remote Discord bridge. The user is issuing commands from their phone or a remote location and cannot see your IDE directly.
When you receive a task through `ai_tasks.txt`, you MUST strictly follow this workflow:

1. **Understand the Request**: Determine if the task requires modifying code, answering a question, or debugging.
2. **Direct Execution (No Branches)**:
   - Edit code directly on the `main` branch.
   - You do NOT need to create a new Git branch.
3. **Execution & Planning**:
   - Make your code changes.
   - If the task is complex, write or update your plan in a markdown file (e.g., `docs/plans/plan.md`) and notify the user.
4. **Commit (MANDATORY)**:
   - **CRITICAL**: ONLY `git add` the specific files explicitly related to the user's prompt. Do NOT use `git add .` or `git commit -a` to avoid accidentally committing unrelated testing or temporary files.
   - Run `git commit -m "<Commit message>"`
5. **Reply Location & URL Generation**:
   - **CRITICAL RULE**: Determine where the task originated from:
     - If the task came from the **IDE chat** (i.e. user typed directly to you in the IDE), you MUST reply ONLY in the IDE chat. Do NOT write to `ai_reply.txt`.
     - If the task came from **Discord** (i.e. you read it from `bot_bridge/ai_tasks.txt` or were awakened by `watcher.py`), you MUST reply ONLY via Discord.
   - When replying via Discord:
     - **CRITICAL**: If the user's task required a plan, use the Discord Bridge Plan Review UI to present it.
     - If the user asks for a code review, use the Discord Bridge Code Diff feature.
     - Write a friendly response to `bot/ai_reply.txt` (located inside the gateway directory, alongside this skill file) explaining what you did.
6. **Re-engage Watcher (ABSOLUTELY CRITICAL)**:
   - **MANDATORY LAST STEP**: Before ending your turn (stopping tool calls), you MUST ALWAYS use the `run_command` tool to launch `python launcher.py` (located alongside this skill file) as a background task. 
   - **WHY**: The `launcher.py` script exits after delivering a message to you. If you do not restart it, the entire Discord remote control system will go offline, and the user will be completely locked out from sending further commands!
   - **HOW**: Use `run_command` with a background task mode (e.g. setting `WaitMsBeforeAsync` appropriately). Make sure the `Cwd` of the command is set to the directory containing `launcher.py`. Never leave the system idle without the launcher running!
