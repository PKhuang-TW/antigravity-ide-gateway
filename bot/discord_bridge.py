import discord
from discord.ext import commands, tasks

import json
import subprocess
import os
import sys
import threading
import hmac
import hashlib
import io
import re

# Add parent directory to sys.path to import bot.config
WORKSPACE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_PATH not in sys.path:
    sys.path.append(WORKSPACE_PATH)

from bot.config import AUTHORIZED_USER_ID, DISCORD_BOT_TOKEN


# Set Intents to allow reading message content
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

# Get workspace path (parent directory)
WORKSPACE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_authorized(ctx):
    if ctx.author.id != AUTHORIZED_USER_ID:
        return False
    # Restrict to specific channel
    try:
        from bot.config import TARGET_CHANNEL_NAME
    except ImportError:
        TARGET_CHANNEL_NAME = "stock-scanner"
    return ctx.channel.name == TARGET_CHANNEL_NAME

def append_ai_task(user_input: str):
    """Write user input or attachment info into the task queue, appending system rules"""
    from datetime import datetime
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    task_file = os.path.join(bot_dir, "ai_tasks.txt")
    os.makedirs(bot_dir, exist_ok=True)
    
    task_content = f"""[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {user_input}

In addition to the above prompt, you MUST follow these rules:
1. After executing the above prompt, please restart the watcher AND all scripts used by this project in the background.
2. Ensure that there is only ONE instance of a script with the same name running in the background.
3. When I talk to you via the IDE, DO NOT reply using ai_reply. ONLY reply using ai_reply when I talk to you via ai_tasks."""
    
    with open(task_file, "a", encoding="utf-8") as f:
        f.write(task_content)

# ======================= UI Components =======================

class TTSView(discord.ui.View):
    def __init__(self, text: str):
        super().__init__(timeout=None)
        self.text = text
        
    @discord.ui.button(label="🔊 Read Aloud (TTS)", style=discord.ButtonStyle.primary, custom_id="tts_button")
    async def tts_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=False)
        try:
            import edge_tts
            import tempfile
            
            # Use Microsoft Edge TTS, speed up by +10%
            communicate = edge_tts.Communicate(self.text, "zh-TW-HsiaoChenNeural", rate="+10%")
            
            # edge_tts.save() requires saving to a file, so we use tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_path = tmp_file.name
                
            await communicate.save(tmp_path)
            
            file = discord.File(tmp_path, filename="tts.mp3")
            await interaction.followup.send(content="🔊 Audio generated successfully (Using high-quality Microsoft Voice + 1.1x speed)", file=file)
            
            # Delete temporary file after sending
            import os
            try:
                os.remove(tmp_path)
            except:
                pass
        except Exception as e:
            await interaction.followup.send(content=f"⚠️ TTS generation failed: {str(e)}", ephemeral=True)

class PlanReviewModal(discord.ui.Modal, title='Add Plan Review Comment'):
    def __init__(self, view_instance):
        super().__init__()
        self.view_instance = view_instance
        self.comment_input = discord.ui.TextInput(
            label='Your suggestions or questions',
            style=discord.TextStyle.paragraph,
            placeholder='Please enter here...',
            required=True
        )
        self.add_item(self.comment_input)

    async def on_submit(self, interaction: discord.Interaction):
        section = self.view_instance.selected_section or "General Suggestions"
        comment = self.comment_input.value
        self.view_instance.accumulated_comments.append(f"[{section}]: {comment}")
        await interaction.response.send_message(f"✅ Recorded comment for `{section}` !(Current total {len(self.view_instance.accumulated_comments)} comments)", ephemeral=True)

class PlanReviewView(discord.ui.View):
    def __init__(self, plan_text: str):
        super().__init__(timeout=None)
        self.plan_text = plan_text
        self.accumulated_comments = []
        self.selected_section = None
        
        headers = re.findall(r'^(#{1,3})\s+(.*)', plan_text, re.MULTILINE)
        options = [discord.SelectOption(label="General Suggestions", value="General Suggestions")]
        for _, h in headers[:24]:
            label = h[:90]
            options.append(discord.SelectOption(label=label, value=label))
            
        self.select = discord.ui.Select(placeholder='Select a section to comment on...', options=options)
        self.select.callback = self.select_callback
        self.add_item(self.select)
        
    async def select_callback(self, interaction: discord.Interaction):
        self.selected_section = self.select.values[0]
        await interaction.response.defer()

    @discord.ui.button(label="✏️ Add Comment", style=discord.ButtonStyle.primary, custom_id="btn_add_comment", row=1)
    async def add_comment(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PlanReviewModal(self))

    @discord.ui.button(label="📤 Submit All Reviews", style=discord.ButtonStyle.success, custom_id="btn_submit_review", row=1)
    async def submit_review(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.accumulated_comments:
            await interaction.response.send_message("⚠️ You haven't added any comments yet!", ephemeral=True)
            return
            
        combined = "\n".join(self.accumulated_comments)
        user_input = f"[Plan Review Submission]\n{combined}"
        task_file = os.path.join(WORKSPACE_PATH, "bot", "ai_tasks.txt")
        from datetime import datetime
        with open(task_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {user_input}\n\nEnsure that there is only ONE instance of a script with the same name running in the background.\n\nAfter executing the above prompt, please restart the watcher in the background.\n")
            
        await interaction.response.send_message("✅ All comments submitted to AI!", ephemeral=False)
        self.stop()

    @discord.ui.button(label="✅ Approve Directly", style=discord.ButtonStyle.secondary, custom_id="btn_approve", row=1)
    async def approve_plan(self, interaction: discord.Interaction, button: discord.ui.Button):
        task_file = os.path.join(WORKSPACE_PATH, "bot", "ai_tasks.txt")
        from datetime import datetime
        with open(task_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [Plan Approved] User has approved the plan without any changes.\n\nEnsure that there is only ONE instance of a script with the same name running in the background.\n\nAfter executing the above prompt, please restart the watcher in the background.\n")
        await interaction.response.send_message("✅ Plan approved!", ephemeral=False)
        self.stop()

class DiffChunkView(discord.ui.View):
    def __init__(self, file_path: str, diff_text: str):
        super().__init__(timeout=None)
        self.file_path = file_path
        self.diff_text = diff_text
        
    @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.success, custom_id="btn_accept_diff")
    async def accept_diff(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        button.label = "Accepted"
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"✅ Accepted changes in `{self.file_path}`", ephemeral=True)

    @discord.ui.button(label="❌ Discard", style=discord.ButtonStyle.danger, custom_id="btn_discard_diff")
    async def discard_diff(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            subprocess.run(["git", "checkout", "--", self.file_path], cwd=WORKSPACE_PATH, check=True)
            for child in self.children:
                child.disabled = True
            button.label = "Discarded"
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"❌ Reverted changes in `{self.file_path}`", ephemeral=False)
            task_file = os.path.join(WORKSPACE_PATH, "bot", "ai_tasks.txt")
            from datetime import datetime
            with open(task_file, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [Diff Rejected] User has discarded changes for file: {self.file_path}\n\nEnsure that there is only ONE instance of a script with the same name running in the background.\n\nAfter executing the above prompt, please restart the watcher in the background.\n")
        except Exception as e:
            await interaction.followup.send(f"⚠️ Failed to revert {self.file_path}: {e}", ephemeral=True)

# =============================================================

@tasks.loop(seconds=2.0)
async def check_ai_reply():
    try:
        from bot.config import TARGET_CHANNEL_NAME
    except ImportError:
        TARGET_CHANNEL_NAME = "stock-scanner"
        
    reply_file = os.path.join(WORKSPACE_PATH, "bot", "ai_reply.txt")
    if os.path.exists(reply_file):
        try:
            with open(reply_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                
            if content:
                target_channel = discord.utils.get(bot.get_all_channels(), name=TARGET_CHANNEL_NAME)
                if target_channel:
                    if "[PLAN_REVIEW]" in content:
                        lines = content.split('\n')
                        path_line = next((l for l in lines if "[PLAN_REVIEW]" in l), None)
                        if path_line:
                            path = path_line.split("[PLAN_REVIEW]")[1].strip()
                            abs_path = os.path.join(WORKSPACE_PATH, path) if not os.path.isabs(path) else path
                            if os.path.exists(abs_path):
                                with open(abs_path, 'r', encoding='utf-8') as pf:
                                    plan_text = pf.read()
                                for i in range(0, len(plan_text), 1900):
                                    chunk = plan_text[i:i+1900]
                                    if i == 0:
                                        await target_channel.send(f"📋 **Implementation Plan Review:**\n{chunk}")
                                    else:
                                        await target_channel.send(chunk)
                                view = PlanReviewView(plan_text=plan_text)
                                await target_channel.send("👇 Please leave your Review below or Approve directly:", view=view)
                                content = content.replace(path_line, "").strip()
                    
                    if content:
                        for i in range(0, len(content), 1900):
                            text_chunk = content[i:i+1900]
                            view = TTSView(text=text_chunk)
                            await target_channel.send(f"🤖 **Antigravity AI:**\n{text_chunk}", view=view)
                        
                with open(reply_file, "w", encoding="utf-8") as f:
                    f.write("")
        except Exception as e:
            print(f"⚠️ Error reading AI message: {e}")
            try:
                # Try to clear the file to avoid infinite loop errors
                with open(reply_file, "w", encoding="utf-8") as f:
                    f.write("")
            except:
                pass

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}, system standby...')
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Synced {len(synced)} Slash Commands")
    except Exception as e:
        print(f"⚠️ Failed to sync Slash Commands: {e}")

    if not check_ai_reply.is_running():
        check_ai_reply.start()

@bot.event
async def on_message(message):
    # Avoid bot talking to itself
    if message.author == bot.user:
        return
        
    try:
        from bot.config import TARGET_CHANNEL_NAME
    except ImportError:
        TARGET_CHANNEL_NAME = "stock-scanner"
        
    # Ensure response is only in the designated channel
    if message.channel.name != TARGET_CHANNEL_NAME:
        return
        
    # Any text or attachment from an authorized user is treated as a task (excluding traditional commands)
    if message.author.id == AUTHORIZED_USER_ID and not message.content.startswith('/'):
        user_input = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        attachment_paths = []
        if message.attachments:
            import os
            download_dir = os.path.join(WORKSPACE_PATH, "bot", "downloads")
            os.makedirs(download_dir, exist_ok=True)
            for att in message.attachments:
                file_path = os.path.join(download_dir, att.filename)
                await att.save(file_path)
                attachment_paths.append(file_path)
                
        if attachment_paths:
            user_input += "\n\n[System Prompt] User uploaded an attachment (e.g., image or file), saved to local path:\n" + "\n".join(attachment_paths)
            user_input = user_input.strip()
            
        if user_input:
            msg_preview = user_input if len(user_input) <= 500 else user_input[:500] + "..."
            await message.channel.send(f"📥 Received command, placed in task queue (Dropzone):\n`{msg_preview}`\nWaiting for IDE scheduler to take over...")
            try:
                append_ai_task(user_input)
            except Exception as e:
                await message.channel.send(f"⚠️ System Error: Failed to write task - {str(e)}")
                
    # Let the bot continue processing other normal commands (e.g., /diff, /restart)
    await bot.process_commands(message)

from discord import app_commands

@bot.tree.command(name="upload", description="Upload file or image for AI to process")
@app_commands.describe(file="The file or image to upload", prompt="Message to the AI (optional)")
async def upload_file(interaction: discord.Interaction, file: discord.Attachment, prompt: str = ""):
    if interaction.user.id != AUTHORIZED_USER_ID:
        await interaction.response.send_message("❌ You do not have permission", ephemeral=True)
        return
        
    import os
    download_dir = os.path.join(WORKSPACE_PATH, "bot", "downloads")
    os.makedirs(download_dir, exist_ok=True)
    file_path = os.path.join(download_dir, file.filename)
    await file.save(file_path)
    
    user_input = prompt + f"\n\n[System Prompt] User uploaded an attachment via /upload command, saved to local path:\n{file_path}"
    user_input = user_input.strip()
    
    await interaction.response.send_message(f"📥 Received `/upload` command and attachment, placed in task queue:\n`{prompt}`\nWaiting for IDE scheduler to take over...")
    
    try:
        append_ai_task(user_input)
    except Exception as e:
        await interaction.followup.send(f"⚠️ System Error: Failed to write task - {str(e)}")

@bot.command()
@commands.check(is_authorized)
async def diff(ctx):
    """View current Git changes"""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only"], 
            cwd=WORKSPACE_PATH, capture_output=True, text=True
        )
        files = [f for f in result.stdout.split('\n') if f.strip()]
        
        if not files:
            await ctx.send("🔍 There are currently no uncommitted changes.")
            return

        for f in files:
            res_f = subprocess.run(["git", "diff", "--", f], cwd=WORKSPACE_PATH, capture_output=True, text=True)
            diff_text = res_f.stdout
            if len(diff_text) > 1900:
                diff_text = diff_text[:1900] + "\n... (Diff too long, truncated)"
            
            embed = discord.Embed(title=f"📄 {f}", description=f"```diff\n{diff_text}\n```", color=discord.Color.blue())
            view = DiffChunkView(file_path=f, diff_text=diff_text)
            await ctx.send(embed=embed, view=view)
    except Exception as e:
        await ctx.send(f"⚠️ Failed to get diff: {str(e)}")

@bot.command()
@commands.check(is_authorized)
async def restart(ctx, filename: str = "scanner.py"):
    """Ask AI to restart the specified python file (default is scanner.py)"""
    await ctx.send(f"🤖 Task to restart `{filename}` assigned to Antigravity IDE! Please wait...")
    try:
        from datetime import datetime
        task_file = os.path.join(WORKSPACE_PATH, "bot", "ai_tasks.txt")
        os.makedirs(os.path.dirname(task_file), exist_ok=True)
        
        with open(task_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Please help me find the process running `{filename}` from the terminal, terminate it, and then restart it.\n\nEnsure that there is only ONE instance of a script with the same name running in the background.\n\nAfter executing the above prompt, please restart the watcher in the background.\n")
    except Exception as e:
        await ctx.send(f"⚠️ System Error: Failed to write task - {str(e)}")


# Start the Bot
bot.run(DISCORD_BOT_TOKEN)
