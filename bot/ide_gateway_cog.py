import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import subprocess
import re
import sys

# Ensure stdout is utf-8 on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# We store the languages inside the parent framework so child projects don't have to look at huge dictionaries.
LANGUAGES = {
    "en": {
        "tts_button": "🔊 Read Aloud (TTS)",
        "tts_success": "🔊 Audio generated successfully (Using high-quality Microsoft Voice + 1.1x speed)",
        "tts_fail": "⚠️ TTS generation failed:",
        "add_comment": "✏️ Add Comment",
        "manage_comments": "📋 Manage Comments",
        "submit_review": "📤 Submit All Reviews",
        "approve": "✅ Approve Directly",
        "no_permission": "❌ You do not have permission",
        "task_queued": "📥 Received command, placed in task queue (Dropzone):\n",
        "waiting_ide": "Waiting for IDE scheduler to take over...",
        "sys_err": "⚠️ System Error: Failed to write task -",
        "diff_desc": "View current Git changes",
        "no_diff": "🔍 There are currently no uncommitted changes.",
        "diff_trunc": "... (Diff too long, truncated)",
        "diff_fail": "⚠️ Failed to get diff:",
        "restart_desc": "Ask AI to restart the specified python file (default is main.py)",
        "restart_msg": "🤖 Task to restart `{filename}` assigned to Antigravity IDE! Please wait...",
        "accept_diff": "✅ Accept",
        "discard_diff": "❌ Discard",
        "accepted": "✅ Accepted changes in",
        "discarded": "❌ Reverted changes in",
        "revert_fail": "⚠️ Failed to revert",
        "upload_desc": "Upload file or image for AI to process",
        "upload_file_desc": "The file or image to upload",
        "upload_prompt_desc": "Message to the AI (optional)",
        "upload_sys_prompt": "[System Prompt] User uploaded an attachment via /upload command, saved to local path:\n",
        "upload_queued": "📥 Received `/upload` command and attachment, placed in task queue:\n",
        "attachment_sys_prompt": "[System Prompt] User uploaded an attachment (e.g., image or file), saved to local path:\n",
        "review_header": "📋 **Implementation Plan Review:**",
        "review_prompt": "👇 Please leave your Review below or Approve directly:",
        "ai_header": "🤖 **Antigravity AI:**",
        "plan_approved": "[Plan Approved] User has approved the plan without any changes.",
        "diff_rejected": "[Diff Rejected] User has discarded changes for file:",
        "default_rules": (
            "In addition to the above prompt, you MUST follow these rules:\n"
            "1. After executing the above prompt, please restart `launcher.py` in the background.\n"
            "2. Ensure that there is only ONE instance of a script with the same name running in the background.\n"
            "3. When I talk to you via the IDE, DO NOT reply using ai_reply. ONLY reply using ai_reply when I talk to you via ai_tasks."
        )
    },
    "zh": {
        "tts_button": "🔊 語音朗讀 (TTS)",
        "tts_success": "🔊 語音生成成功 (使用高音質微軟語音 + 1.1x 語速)",
        "tts_fail": "⚠️ 語音生成失敗:",
        "add_comment": "✏️ 新增註解",
        "manage_comments": "📋 管理註解",
        "submit_review": "📤 送出所有審查意見",
        "approve": "✅ 直接核准",
        "no_permission": "❌ 您沒有權限",
        "task_queued": "📥 收到指令，已放入待辦任務區 (Dropzone)：\n",
        "waiting_ide": "等待 IDE 排程接手處理...",
        "sys_err": "⚠️ 系統錯誤：寫入任務失敗 -",
        "diff_desc": "查看目前檔案的 Git 變更",
        "no_diff": "🔍 目前沒有任何尚未 commit 的變更。",
        "diff_trunc": "... (Diff 過長已截斷)",
        "diff_fail": "⚠️ 無法取得 diff：",
        "restart_desc": "請 AI 重啟指定的 python 檔案 (預設為 main.py)",
        "restart_msg": "🤖 已將重啟 `{filename}` 的任務指派給 Antigravity IDE！請稍候...",
        "accept_diff": "✅ 接受",
        "discard_diff": "❌ 捨棄",
        "accepted": "✅ 已接受變更：",
        "discarded": "❌ 已復原變更：",
        "revert_fail": "⚠️ 復原失敗",
        "upload_desc": "上傳檔案或圖片給 AI 處理",
        "upload_file_desc": "要上傳的檔案或圖片",
        "upload_prompt_desc": "要對 AI 說的話 (選填)",
        "upload_sys_prompt": "[系統提示] 使用者透過 /upload 指令上傳了附件，已儲存至本地路徑：\n",
        "upload_queued": "📥 收到 `/upload` 指令與附件，已放入待辦任務區：\n",
        "attachment_sys_prompt": "[系統提示] 使用者上傳了附件 (如圖片或檔案)，已儲存至本地路徑：\n",
        "review_header": "📋 **實作計畫審查 (Plan Review):**",
        "review_prompt": "👇 請在下方留下您的審查意見，或直接核准：",
        "ai_header": "🤖 **Antigravity AI:**",
        "plan_approved": "[Plan Approved] User has approved the plan without any changes.",
        "diff_rejected": "[Diff Rejected] User has discarded changes for file:",
        "default_rules": (
            "除上述 prompt 以外，請務必遵守以下規則:\n"
            "1. 請在執行完畢上述 prompt 之後，在背景重新執行 `launcher.py`\n"
            "2. 請確保背景執行中同名字的 script 只有一個\n"
            "3. 當我用 IDE 直接跟你對話時，請你不要用 ai_reply 回覆我。只有當任務來自 ai_tasks 檔案時才用 ai_reply 回覆。"
        )
    }
}

class IDEGatewayCore(commands.Cog):
    def __init__(self, bot, config=None, lang="en"):
        self.bot = bot
        # Default configuration
        self.config = {
            "authorized_user_id": None, # [USER_FILL_REQUIRED] Your Discord User ID
            "target_channel_name": "my-project-channel", # [USER_FILL_REQUIRED] Channel name to listen to
            "ai_tasks_file": "ai_tasks.txt",
            "ai_reply_file": "ai_reply.txt",
            "system_rules": "", # Any extra rules a child project wants to append
            "workspace_path": os.getcwd()
        }
        if config:
            self.config.update(config)

        # Load language strings easily
        self.lang = LANGUAGES.get(lang, LANGUAGES["en"])

        # Initialize the check reply task
        self.check_ai_reply.start()

    def cog_unload(self):
        self.check_ai_reply.cancel()

    def is_authorized(self, user_id):
        if self.config["authorized_user_id"] is None:
            return True
        return user_id == self.config["authorized_user_id"]

    def append_ai_task(self, user_input: str):
        """
        Write the task to ai_tasks.txt. 
        If the child project specified extra 'system_rules', append them automatically!
        """
        from datetime import datetime
        task_file = self.config["ai_tasks_file"]
        os.makedirs(os.path.dirname(task_file), exist_ok=True)
        
        task_content = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {user_input}\n"
        
        # Append parent default rules automatically
        if "default_rules" in self.lang:
            task_content += f"\n{self.lang['default_rules']}\n"
        
        # Append the custom rules provided by the child project config
        if self.config.get("system_rules"):
            task_content += f"\n[Child Project Custom Rules]:\n{self.config['system_rules']}\n"
        
        with open(task_file, "a", encoding="utf-8") as f:
            f.write(task_content)

    @tasks.loop(seconds=2.0)
    async def check_ai_reply(self):
        reply_file = self.config["ai_reply_file"]
        if os.path.exists(reply_file):
            try:
                with open(reply_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    
                if content:
                    target_channel = discord.utils.get(self.bot.get_all_channels(), name=self.config["target_channel_name"])
                    if target_channel:
                        if "[PLAN_REVIEW]" in content:
                            lines = content.split('\n')
                            path_line = next((l for l in lines if "[PLAN_REVIEW]" in l), None)
                            if path_line:
                                path = path_line.split("[PLAN_REVIEW]")[1].strip()
                                abs_path = os.path.join(self.config["workspace_path"], path) if not os.path.isabs(path) else path
                                if os.path.exists(abs_path):
                                    with open(abs_path, 'r', encoding='utf-8') as pf:
                                        plan_text = pf.read()
                                    for i in range(0, len(plan_text), 1900):
                                        chunk = plan_text[i:i+1900]
                                        if i == 0:
                                            await target_channel.send(f"{self.lang['review_header']}\n{chunk}")
                                        else:
                                            await target_channel.send(chunk)
                                    view = PlanReviewView(self, plan_text=plan_text)
                                    await target_channel.send(self.lang['review_prompt'], view=view)
                                    content = content.replace(path_line, "").strip()
                        
                        if content:
                            for i in range(0, len(content), 1900):
                                text_chunk = content[i:i+1900]
                                view = TTSView(self, text=text_chunk)
                                await target_channel.send(f"{self.lang['ai_header']}\n{text_chunk}", view=view)
                            
                    with open(reply_file, "w", encoding="utf-8") as f:
                        f.write("")
            except Exception as e:
                print(f"⚠️ Error reading AI message: {e}")
                try:
                    with open(reply_file, "w", encoding="utf-8") as f:
                        f.write("")
                except:
                    pass

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'✅ Logged in as {self.bot.user}, system standby...')
        try:
            synced = await self.bot.tree.sync()
            print(f"🔄 Synced {len(synced)} Slash Commands")
        except Exception as e:
            print(f"⚠️ Failed to sync Slash Commands: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
            
        if message.channel.name != self.config["target_channel_name"]:
            return
            
        if self.is_authorized(message.author.id) and not message.content.startswith('/'):
            user_input = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
            
            attachment_paths = []
            if message.attachments:
                download_dir = os.path.join(os.path.dirname(self.config["ai_tasks_file"]), "downloads")
                os.makedirs(download_dir, exist_ok=True)
                for att in message.attachments:
                    file_path = os.path.join(download_dir, att.filename)
                    await att.save(file_path)
                    attachment_paths.append(file_path)
                    
            if attachment_paths:
                user_input += f"\n\n{self.lang['attachment_sys_prompt']}" + "\n".join(attachment_paths)
                user_input = user_input.strip()
                
            if user_input:
                msg_preview = user_input if len(user_input) <= 500 else user_input[:500] + "..."
                await message.channel.send(f"{self.lang['task_queued']}`{msg_preview}`\n{self.lang['waiting_ide']}")
                try:
                    self.append_ai_task(user_input)
                except Exception as e:
                    await message.channel.send(f"{self.lang['sys_err']} {str(e)}")

    @app_commands.command(name="upload", description="Upload file or image for AI to process")
    async def upload_file(self, interaction: discord.Interaction, file: discord.Attachment, prompt: str = ""):
        if not self.is_authorized(interaction.user.id):
            await interaction.response.send_message(self.lang['no_permission'], ephemeral=True)
            return
            
        download_dir = os.path.join(os.path.dirname(self.config["ai_tasks_file"]), "downloads")
        os.makedirs(download_dir, exist_ok=True)
        file_path = os.path.join(download_dir, file.filename)
        await file.save(file_path)
        
        user_input = prompt + f"\n\n{self.lang['upload_sys_prompt']}{file_path}"
        user_input = user_input.strip()
        
        await interaction.response.send_message(f"{self.lang['upload_queued']}`{prompt}`\n{self.lang['waiting_ide']}")
        
        try:
            self.append_ai_task(user_input)
        except Exception as e:
            await interaction.followup.send(f"{self.lang['sys_err']} {str(e)}")

    @commands.command()
    async def diff(self, ctx):
        if not self.is_authorized(ctx.author.id):
            return
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only"], 
                cwd=self.config["workspace_path"], capture_output=True, text=True
            )
            files = [f for f in result.stdout.split('\n') if f.strip()]
            
            if not files:
                await ctx.send(self.lang['no_diff'])
                return

            for f in files:
                res_f = subprocess.run(["git", "diff", "--", f], cwd=self.config["workspace_path"], capture_output=True, text=True)
                diff_text = res_f.stdout
                if len(diff_text) > 1900:
                    diff_text = diff_text[:1900] + "\n" + self.lang['diff_trunc']
                
                embed = discord.Embed(title=f"📄 {f}", description=f"```diff\n{diff_text}\n```", color=discord.Color.blue())
                view = DiffChunkView(self, file_path=f, diff_text=diff_text)
                await ctx.send(embed=embed, view=view)
        except Exception as e:
            await ctx.send(f"{self.lang['diff_fail']} {str(e)}")

    @commands.command()
    async def restart(self, ctx, filename: str = "main.py"):
        if not self.is_authorized(ctx.author.id):
            return
        await ctx.send(self.lang['restart_msg'].format(filename=filename))
        try:
            user_input = f"Please help me find the process running `{filename}` from the terminal, terminate it, and then restart it."
            self.append_ai_task(user_input)
        except Exception as e:
            await ctx.send(f"{self.lang['sys_err']} {str(e)}")


# ======================= UI Components =======================

class TTSView(discord.ui.View):
    def __init__(self, cog: IDEGatewayCore, text: str):
        super().__init__(timeout=None)
        self.cog = cog
        self.text = text
        
        btn = discord.ui.Button(label=self.cog.lang['tts_button'], style=discord.ButtonStyle.primary, custom_id="tts_button")
        btn.callback = self.tts_button
        self.add_item(btn)
        
    async def tts_button(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        try:
            import edge_tts
            import tempfile
            communicate = edge_tts.Communicate(self.text, "zh-TW-HsiaoChenNeural", rate="+10%")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_path = tmp_file.name
            await communicate.save(tmp_path)
            file = discord.File(tmp_path, filename="tts.mp3")
            await interaction.followup.send(content=self.cog.lang['tts_success'], file=file)
            os.remove(tmp_path)
        except Exception as e:
            await interaction.followup.send(content=f"{self.cog.lang['tts_fail']} {str(e)}", ephemeral=True)

class PlanReviewModal(discord.ui.Modal):
    def __init__(self, view_instance):
        super().__init__(title='Add Plan Review Comment')
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

class EditCommentModal(discord.ui.Modal):
    def __init__(self, main_view, index, manage_msg):
        super().__init__(title='Edit Comment')
        self.main_view = main_view
        self.index = index
        self.manage_msg = manage_msg
        
        old_comment = self.main_view.accumulated_comments[index]
        self.section_val = ""
        text = old_comment
        if "]: " in old_comment:
            parts = old_comment.split("]: ", 1)
            self.section_val = parts[0] + "]"
            text = parts[1]
            
        self.comment_input = discord.ui.TextInput(
            label='Edit your suggestion or question',
            style=discord.TextStyle.paragraph,
            default=text,
            required=True
        )
        self.add_item(self.comment_input)

    async def on_submit(self, interaction: discord.Interaction):
        new_text = self.comment_input.value
        if self.section_val:
            new_comment = f"{self.section_val}: {new_text}"
        else:
            new_comment = new_text
            
        self.main_view.accumulated_comments[self.index] = new_comment
        new_view = ManageCommentsView(self.main_view)
        await self.manage_msg.edit(view=new_view)
        await interaction.response.send_message("✅ Comment updated successfully!", ephemeral=True)

class ManageCommentsView(discord.ui.View):
    def __init__(self, main_view):
        super().__init__(timeout=None)
        self.main_view = main_view
        self.selected_index = None
        
        options = []
        for i, comment in enumerate(self.main_view.accumulated_comments):
            label = comment[:90] + "..." if len(comment) > 90 else comment
            options.append(discord.SelectOption(label=label, value=str(i)))
            
        self.select = discord.ui.Select(placeholder='Select a comment to manage...', options=options)
        self.select.callback = self.select_callback
        self.add_item(self.select)
        
    async def select_callback(self, interaction: discord.Interaction):
        self.selected_index = int(self.select.values[0])
        await interaction.response.defer()

    @discord.ui.button(label="📝 Edit Selected", style=discord.ButtonStyle.primary, row=1)
    async def edit_comment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.selected_index is None:
            await interaction.response.send_message("⚠️ Please select a comment from the dropdown first!", ephemeral=True)
            return
        modal = EditCommentModal(self.main_view, self.selected_index, interaction.message)
        await interaction.response.send_modal(modal)
        
    @discord.ui.button(label="🗑️ Delete Selected", style=discord.ButtonStyle.danger, row=1)
    async def delete_comment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.selected_index is None:
            await interaction.response.send_message("⚠️ Please select a comment from the dropdown first!", ephemeral=True)
            return
        self.main_view.accumulated_comments.pop(self.selected_index)
        if not self.main_view.accumulated_comments:
            await interaction.message.edit(content="All comments cleared.", view=None)
        else:
            new_view = ManageCommentsView(self.main_view)
            await interaction.message.edit(view=new_view)
        await interaction.response.send_message(f"🗑️ Deleted the selected comment!", ephemeral=True)

class PlanReviewView(discord.ui.View):
    def __init__(self, cog: IDEGatewayCore, plan_text: str):
        super().__init__(timeout=None)
        self.cog = cog
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
        
        btn_add = discord.ui.Button(label=self.cog.lang['add_comment'], style=discord.ButtonStyle.primary, row=1)
        btn_add.callback = self.add_comment
        self.add_item(btn_add)
        
        btn_manage = discord.ui.Button(label=self.cog.lang['manage_comments'], style=discord.ButtonStyle.secondary, row=1)
        btn_manage.callback = self.manage_comments
        self.add_item(btn_manage)
        
        btn_submit = discord.ui.Button(label=self.cog.lang['submit_review'], style=discord.ButtonStyle.success, row=1)
        btn_submit.callback = self.submit_review
        self.add_item(btn_submit)
        
        btn_approve = discord.ui.Button(label=self.cog.lang['approve'], style=discord.ButtonStyle.secondary, row=1)
        btn_approve.callback = self.approve_plan
        self.add_item(btn_approve)
        
    async def select_callback(self, interaction: discord.Interaction):
        self.selected_section = self.select.values[0]
        await interaction.response.defer()

    async def add_comment(self, interaction: discord.Interaction):
        await interaction.response.send_modal(PlanReviewModal(self))

    async def manage_comments(self, interaction: discord.Interaction):
        if not self.accumulated_comments:
            await interaction.response.send_message("⚠️ You haven't added any comments yet!", ephemeral=True)
            return
        view = ManageCommentsView(self)
        await interaction.response.send_message("Please select a comment to view, edit or delete:", view=view, ephemeral=True)

    async def submit_review(self, interaction: discord.Interaction):
        if not self.accumulated_comments:
            await interaction.response.send_message("⚠️ You haven't added any comments yet!", ephemeral=True)
            return
        combined = "\n".join(self.accumulated_comments)
        user_input = f"[Plan Review Submission]\n{combined}"
        self.cog.append_ai_task(user_input)
        await interaction.response.send_message("✅ All comments submitted to AI!", ephemeral=False)
        self.stop()

    async def approve_plan(self, interaction: discord.Interaction):
        self.cog.append_ai_task(self.cog.lang['plan_approved'])
        await interaction.response.send_message("✅ Plan approved!", ephemeral=False)
        self.stop()

class DiffChunkView(discord.ui.View):
    def __init__(self, cog: IDEGatewayCore, file_path: str, diff_text: str):
        super().__init__(timeout=None)
        self.cog = cog
        self.file_path = file_path
        self.diff_text = diff_text
        
        btn_acc = discord.ui.Button(label=self.cog.lang['accept_diff'], style=discord.ButtonStyle.success)
        btn_acc.callback = self.accept_diff
        self.add_item(btn_acc)

        btn_dis = discord.ui.Button(label=self.cog.lang['discard_diff'], style=discord.ButtonStyle.danger)
        btn_dis.callback = self.discard_diff
        self.add_item(btn_dis)
        
    async def accept_diff(self, interaction: discord.Interaction):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"{self.cog.lang['accepted']} `{self.file_path}`", ephemeral=True)

    async def discard_diff(self, interaction: discord.Interaction):
        try:
            subprocess.run(["git", "checkout", "--", self.file_path], cwd=self.cog.config['workspace_path'], check=True)
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"{self.cog.lang['discarded']} `{self.file_path}`", ephemeral=False)
            self.cog.append_ai_task(f"{self.cog.lang['diff_rejected']} {self.file_path}")
        except Exception as e:
            await interaction.followup.send(f"{self.cog.lang['revert_fail']} {self.file_path}: {e}", ephemeral=True)
