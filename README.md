# Antigravity IDE Gateway

A modular, plug-and-play Discord bridge specifically designed for **Google DeepMind's Antigravity IDE** (and other fully autonomous AI agents). It connects you with your local Antigravity agent via a natural language Discord interface.

This project enables a **"Text-File Bridge"** architecture:
- The Discord bot acts purely as an intent router (Gateway) and task collector.
- It parses your Discord messages and logs tasks into `ai_tasks.txt`.
- A background `watcher.py` triggers the IDE Agent whenever a new task is dropped.
- The IDE Agent executes the task locally on your machine, handles Git PRs, and replies through `ai_reply.txt` which the Discord bot forwards back to you.

## 🌟 Why Use This Project? (Advantages)

This bridge was born out of a need for seamless, secure, and smart remote AI collaboration. Its core advantages include:

1. **Designed for Autonomous Agents (Antigravity)**: Unlike interactive IDEs like Cursor or GitHub Copilot (which require human-in-the-loop chat prompts), this bridge leverages Antigravity's core superpower: **Asynchronous Background Wakeup**. The AI can monitor background terminal processes and automatically wake up to handle tasks without any human intervention.
2. **Cross-Platform Synchronization**: Issue commands, review Pull Requests (PRs), and share the exact same project files seamlessly across both your mobile phone and your computer via Discord.
3. **Shared AI Context & Memory**: We intentionally avoided building a standalone CLI agent inside the Discord bot. By delegating tasks back to your local IDE Agent, the AI responding from your phone has the *exact same memory, workspace access, and context* as the AI you use when sitting at your computer.
4. **Total Transparency**: All AI code modifications and implementation plans are pushed directly to you via the Discord Bridge. You can comfortably review code diffs and markdown plans directly on Discord's UI. Your responses will reliably hit the local bot to wake up the AI.
5. **100% Independent Multi-Bot Architecture**: Each bot instance actively pulls its own events from Discord. You do not need to configure any local ports, open any firewalls, or worry about connection limits. You can run 10 bots for 10 different projects on the same machine simultaneously!
6. **Token Efficiency (Cost Saving)**: We designed `watcher.py` to act as an interrupt-driven trigger. Instead of forcing the expensive AI agent to constantly poll `ai_tasks.txt` in an infinite loop, the lightweight Python watcher waits and only wakes up the AI when a task is actually received, drastically saving LLM tokens.
7. **Full Image & File Support**: The bridge automatically intercepts drag-and-drop files, `Ctrl+V` pasted images, and `/upload` slash commands, downloading them locally and parsing them to your AI seamlessly.

## 🚨 Security Warning: Protect Your Config

This bridge allows the internet to wake up your local IDE agent and execute commands. **It is critical that you never leak your `bot/config.py` file!**
If a malicious actor obtains your configuration, they could forge webhook payloads and execute arbitrary commands on your local machine via the IDE agent.
**Always ensure `bot/config.py` is in your `.gitignore`!**

## 📁 Directory Structure
- `bot/config.py.example`: Configuration template (Must be renamed to `config.py` and populated).
- `bot/discord_bridge.py`: The main Discord gateway bot that handles Discord messages.
- `bot/watcher.py`: Background task listener that wakes up your IDE.
- `discord_agent_skill.md`: The critical rulebook you must place in your project root for your IDE AI Agent to read.

## 🧠 The AI Agent Skill Manual (`discord_agent_skill.md`)

**Why do we have this file?**
AI Coding Agents are incredibly powerful, but they need strict guidelines to handle tasks remotely via a text-file bridge without breaking your project. This markdown file acts as a **Standard Operating Procedure (SOP)**. It teaches the AI how to read tasks, how to reply via `ai_reply.txt`, how to enforce a strict workflow, and how to restart the background `watcher.py` after finishing its work.

**Do you need to set it up manually?**
**No!** You do not need to configure anything or explicitly tell the AI to read it. As long as the file is inside the template folder, the system handles it automatically.

**How does the AI magically learn it?**
The secret lies within `watcher.py`. Whenever `watcher.py` intercepts a task from Discord and wakes up your local AI agent, it automatically injects a loud terminal system instruction with the dynamic absolute path to this file. Since the AI is programmed to obey terminal outputs, it will be forcefully commanded by `watcher.py` to read the skill manual before it processes any of your Discord tasks!

## ⚙️ Configuration Parameters Explained

Inside `bot/config.py`, you will find several critical parameters. Here is what each one does:

- `DISCORD_BOT_TOKEN`: Your private Discord bot token obtained from the Discord Developer Portal. This authenticates your bot to Discord.
- `AUTHORIZED_USER_ID`: Your personal Discord User ID (a long number). **Security Feature**: The bot will ONLY listen to commands sent by this specific user, ignoring everyone else in the server.
- `TARGET_CHANNEL_NAME`: The specific Discord channel name (e.g., `"stock-scanner"`) where this bot will listen and reply. Commands sent in other channels are ignored.


## 🚀 How to Use (Setup Instructions)

To get this project running, **your computer must be kept on**, and specific Python scripts must be running locally.

### Step 1: Clone the Template
Clone or copy this entire folder into your project directory. You can rename the folder to something like `discord_bot/` or `bot/`. The `watcher.py` script is smart enough to automatically find the `discord_agent_skill.md` file no matter what you name the folder!

### Step 2: Install Dependencies
Ensure you install the required Python packages:
```bash
pip install discord.py aiohttp edge-tts
```


### Step 5: Start the Services (Keep these running!)
Whenever you want the bridge to be active (e.g., when you leave your computer), you must have **two** things running locally:

1. **Start the Bridge**: Run this in a standard terminal to start the Discord bot.
   ```bash
   python3 bot/discord_bridge.py
   ```
2. **Start the Watcher**: Ask your IDE AI agent (via the IDE chat) to start the watcher as a background task. The AI must execute this so it can be interrupted when a task arrives.
   > "Please run `python3 bot/watcher.py` as a background task."

### Step 6: Command the AI!
Now, you can simply go to your Discord channel and say: `@Bot please add some unit tests for utils.py!`
The bot will drop the task into `bot/ai_tasks.txt`, the watcher will wake up your IDE agent, and your IDE agent will get to work, eventually replying to you in Discord!
