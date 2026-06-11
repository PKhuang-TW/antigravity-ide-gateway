# Antigravity IDE Gateway

A modular, extensible, plug-and-play Discord bridge specifically designed for **Google DeepMind's Antigravity IDE** (and other fully autonomous AI agents). It connects you with your local Antigravity agent via a natural language Discord interface.

This project enables a **"Text-File Bridge"** architecture:
- The Discord bot acts purely as an intent router (Gateway) and task collector.
- It parses your Discord messages and logs tasks into `ai_tasks.txt`.
- A background `watcher.py` triggers the IDE Agent whenever a new task is dropped.
- The IDE Agent executes the task locally on your machine, handles Code Diffs/Reviews directly via Discord UI, and replies through `ai_reply.txt` which the Discord bot forwards back to you.

## 🌟 Extensible Framework Architecture (New!)

This project is now designed as an **Extensible Parent Framework**. Child projects (like your own custom Discord bots) do not need to duplicate massive amounts of code. They can simply inherit the core functionality while overriding specific settings.

### The Core Modules
1. **`IDEGatewayCore`** (in `bot/ide_gateway_cog.py`): A Discord `commands.Cog` that encapsulates all the AI task handling, Dropzone logic, Diff/Restart commands, and UI (TTS, Review Modals).
2. **`IDEWatcher`** (in `bot/ide_watcher.py`): A reusable class for the background task listener that wakes up your IDE.

Child projects can subclass `IDEGatewayCore`, override localization strings (e.g., to translate everything to Chinese), pass custom file paths, and add their own specific `@commands.command()`, all without breaking the out-of-the-box functionality of the gateway!

### One-Click Startup
We've introduced `launcher.py`! You no longer need to start the discord bot and the watcher in two separate terminals. A single run of `launcher.py` spawns both processes simultaneously in the background.

## 🌟 Why Use This Project? (Advantages)

1. **Designed for Autonomous Agents (Antigravity)**: Unlike interactive IDEs like Cursor or GitHub Copilot, this bridge leverages Antigravity's core superpower: **Asynchronous Background Wakeup**. The AI can monitor background terminal processes and automatically wake up to handle tasks without human intervention.
2. **Cross-Platform Synchronization**: Issue commands, review code Diffs, and share the exact same project files seamlessly across both your mobile phone and your computer via Discord.
3. **Shared AI Context & Memory**: We intentionally avoided building a standalone CLI agent inside the Discord bot. By delegating tasks back to your local IDE Agent, the AI responding from your phone has the *exact same memory, workspace access, and context* as the AI you use when sitting at your computer.
4. **Total Transparency**: All AI code modifications and implementation plans are pushed directly to you via the Discord Bridge. You can comfortably review code diffs and markdown plans directly on Discord's UI.
5. **100% Independent Multi-Bot Architecture**: Each bot instance actively pulls its own events from Discord. You do not need to configure any local ports, open any firewalls, or worry about connection limits.
6. **Token Efficiency (Cost Saving)**: The `watcher.py` acts as an interrupt-driven trigger. It only wakes up the AI when a task is actually received, drastically saving LLM tokens.
7. **Full Image & File Support**: The bridge automatically intercepts drag-and-drop files, `Ctrl+V` pasted images, and `/upload` slash commands.

## 🚨 Security Warning: Protect Your Config

This bridge allows the internet to wake up your local IDE agent and execute commands. **It is critical that you never leak your `bot/config.py` file!**
If a malicious actor obtains your token, they could hijack the bot to read your private project files, or forge messages to trick your local IDE agent into executing arbitrary code.
**Always ensure `bot/config.py` is in your `.gitignore`!**

## 📁 Directory Structure
- `launcher.py`: The one-click startup script that launches both the bridge and the watcher.
- `bot/config.py.example`: Configuration template (Must be renamed to `config.py` and populated).
- `bot/discord_bridge.py`: The parent runner that initializes `IDEGatewayCore`.
- `bot/watcher.py`: The parent runner that initializes `IDEWatcher`.
- `bot/ide_gateway_cog.py`: The core extensible Cog class containing all Discord logic.
- `bot/ide_watcher.py`: The core extensible watcher logic.
- `discord_agent_skill.md`: The critical SOP manual you must place in your project for your IDE Agent to read.

## 🧠 The AI Agent Skill Manual (`discord_agent_skill.md`)

**Why do we have this file?**
AI Coding Agents are incredibly powerful, but they need strict guidelines to handle tasks remotely via a text-file bridge. This markdown file acts as a **Standard Operating Procedure (SOP)**. It teaches the AI how to read tasks, reply, enforce strict workflows, and restart the background watcher.

## ⚙️ Configuration Parameters Explained

Inside `bot/config.py.example`, you will find several critical parameters that **YOU MUST FILL IN**:
- `DISCORD_BOT_TOKEN`: Your private Discord bot token.
- `AUTHORIZED_USER_ID`: Your personal Discord User ID. **Security Feature**: The bot will ONLY listen to commands sent by this specific user.
- `TARGET_CHANNEL_NAME`: The specific Discord channel name (e.g., `"my-project-channel"`) where this bot will listen.

## 🚀 How to Use (Setup Instructions)

### Step 1: Clone or Submodule
You can clone this repository directly, or add it as a Git submodule to your project so your project can inherit from it.

### Step 2: Install Dependencies
```bash
pip install discord.py aiohttp edge-tts
```

### Step 3: Configure
Copy `bot/config.py.example` to `bot/config.py` and fill in your Discord credentials.

### Step 4: Add Custom Rules (Optional)
If you want to add project-specific rules that the AI MUST follow for every task, edit `bot/discord_bridge.py` and modify the `system_rules` inside the `config` dictionary:
```python
config = {
    ...
    "system_rules": (
        "4. When editing UI files, always use Tailwind CSS.\n"
        "5. Always run pytest after modifying a module."
    )
}
await bot.add_cog(IDEGatewayCore(bot, config=config, lang="en"))
```

### Step 5: Start the Services (One-Click)
Run the launcher script to start both the Discord bridge and the background watcher simultaneously:
```bash
python launcher.py
```

### Step 6: Command the AI!
Now, you can simply go to your Discord channel and say: `@Bot please add some unit tests for utils.py!`
The bot will drop the task into `bot/ai_tasks.txt`, the watcher will wake up your IDE agent, and your IDE agent will get to work!
