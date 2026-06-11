import time
import os
import sys

# Ensure stdout is utf-8 on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

class IDEWatcher:
    def __init__(self, task_file_path: str, skill_file_path: str = None):
        self.task_file_path = task_file_path
        self.skill_file_path = skill_file_path

    def start(self):
        if sys.stdout.encoding.lower() != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')

        print("Starting AI Task Watcher...", flush=True)

        while True:
            if os.path.exists(self.task_file_path):
                try:
                    with open(self.task_file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        
                    if content:
                        print(f"🚨 New task received!\n{content}", flush=True)
                        print("\n[AI_SYSTEM_INSTRUCTION]: This is a remote task from Discord!", flush=True)
                        
                        if self.skill_file_path and os.path.exists(self.skill_file_path):
                            skill_path_safe = self.skill_file_path.replace("\\", "/")
                            print(f"[AI_SYSTEM_INSTRUCTION]: To ensure a perfect PR workflow, you MUST read and strictly follow the skill manual at `{skill_path_safe}` before processing this task!", flush=True)
                        
                        # Clear file
                        with open(self.task_file_path, "w", encoding="utf-8") as f:
                            f.write("")
                            
                        # Exit program immediately so IDE treats the output as execution result and replies
                        sys.exit(0)
                except Exception as e:
                    print(f"Watcher error: {e}", flush=True)
                    
            time.sleep(1)

if __name__ == "__main__":
    # For testing/standalone usage
    task_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_tasks.txt")
    skill_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "discord_agent_skill.md")
    watcher = IDEWatcher(task_file, skill_file)
    watcher.start()
