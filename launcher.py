import subprocess
import sys
import os
import time

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    bridge_script = os.path.join(base_dir, "bot", "discord_bridge.py")
    watcher_script = os.path.join(base_dir, "bot", "watcher.py")
    
    print("🚀 Starting Antigravity IDE Gateway Launcher...")
    
    # We use subprocess.Popen to run both in the background
    # Since we are just a launcher, we can block and wait for them, or just let them run.
    # To "keep them as two scripts but one-click launch", we can launch both and wait.
    
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    
    bridge_proc = subprocess.Popen([sys.executable, bridge_script], env=env)
    watcher_proc = subprocess.Popen([sys.executable, watcher_script], env=env)
    
    print("✅ Gateway and Watcher started successfully. Press Ctrl+C to stop both.")
    
    try:
        while True:
            time.sleep(1)
            # If watcher dies (e.g. detected a task), we want to keep bridge running,
            # but ideally the user/IDE will restart the watcher. 
            # Or should the launcher automatically restart the watcher?
            # The IDE currently restarts the watcher as a background task via task list,
            # so the launcher doesn't need to auto-restart it.
            if bridge_proc.poll() is not None:
                print("Discord bridge stopped.")
                break
    except KeyboardInterrupt:
        print("Stopping processes...")
        bridge_proc.terminate()
        watcher_proc.terminate()
        bridge_proc.wait()
        watcher_proc.wait()
        print("Stopped.")

if __name__ == "__main__":
    main()
