import time
import os
import sys

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Use absolute path to ensure reliability
file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_tasks.txt")
print("Starting AI Task Watcher...", flush=True)

while True:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            
        if content:
            # Print content, flush=True ensures system intercepts and wakes up AI
            print(f"🚨 New task received!\n{content}", flush=True)
            print("\n[AI_SYSTEM_INSTRUCTION]: This is a remote task from Discord!", flush=True)
            
            # Dynamically resolve the path to the skill manual
            skill_dir = os.path.dirname(os.path.abspath(__file__))
            skill_file_path = os.path.join(skill_dir, "discord_agent_skill.md")
            # Use forward slashes for better compatibility with AI parsing
            skill_file_path = skill_file_path.replace("\\", "/")
            
            print(f"[AI_SYSTEM_INSTRUCTION]: To ensure a perfect PR workflow, you MUST read and strictly follow the skill manual at `{skill_file_path}` before processing this task!", flush=True)
            
            # Clear file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("")
                
            # Exit program immediately so IDE treats the output as execution result and replies
            sys.exit(0)
                
    time.sleep(1)
