import os
from ide_watcher import IDEWatcher

if __name__ == "__main__":
    task_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_tasks.txt")
    skill_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "discord_agent_skill.md")
    
    watcher = IDEWatcher(task_file, skill_file)
    watcher.start()
