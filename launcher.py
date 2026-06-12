import subprocess
import sys
import os
import time

# Ensure stdout is utf-8 on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

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
            if bridge_proc.poll() is not None:
                print("Discord bridge stopped.", flush=True)
                break
            if watcher_proc.poll() is not None:
                print("Watcher stopped (Likely received a task). Exiting launcher to wake up IDE...", flush=True)
                break
    except KeyboardInterrupt:
        print("Keyboard interrupt received.")
    finally:
        print("Cleaning up processes...", flush=True)
        if bridge_proc.poll() is None:
            bridge_proc.terminate()
        if watcher_proc.poll() is None:
            watcher_proc.terminate()
        bridge_proc.wait()
        watcher_proc.wait()
        print("Stopped.", flush=True)

if __name__ == "__main__":
    main()
