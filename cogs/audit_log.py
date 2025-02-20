import discord
from discord.ext import commands
import config


class AuditLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log_event(self, embed):
        """Sends message to log channel"""
        log_channel = self.bot.get_channel(config.LOG_CHANNEL)
        if log_channel:
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, after, before):
        """Logs edited messages"""
        if before.author.bot or before.content == after.content:
            return

        embed = discord.Embed(title="✏️ Message Edited", color=discord.Color.blue())
        message_link = f"https://discord.com/channels/{before.guild.id}/{before.channel.id}/{before.id}"
        embed.add_field(name="Author", value=f"{before.author} ({before.author.id})", inline=False)
        embed.add_field(name="Channel", value=f"{before.channel} ({before.channel.id})", inline=False)
        embed.add_field(name="Link", value=f"[Go to message]({message_link})", inline=False)
        embed.add_field(name="Original message", value=before.content[:1024])
        embed.add_field(name="Edited message", value=after.content, inline=False)
        embed.add_field(name="ID", value=before.id, inline=True)
        embed.timestamp = after.edited_at

        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Logs deleted messages"""
        if message.author.bot:
            return

        embed = discord.Embed(title="🗑️ Message Deleted", color=discord.Color.red())
        embed.add_field(name="Author", value=f"{message.author} ({message.author.id})", inline=False)
        embed.add_field(name="Channel", value=f"{message.channel} ({message.channel.id})", inline=False)
        embed.add_field(name="Contents", value=message.content[:1024] if message.content else "*No text*", inline=False)
        embed.add_field(name="ID", value=message.id, inline=True)
        embed.timestamp = message.created_at

        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Logs joined member"""
        account_creation = member.created_at.strftime("%d/%m/%Y %H:%M:%S")

        embed = discord.Embed(title="🟢 Member Joined", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Account created", value=account_creation, inline=True)
        embed.timestamp = member.joined_at

        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Logs member ban"""
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 10:
                moderator = entry.user
                reason = entry.reason if entry.reason else "No reason"
                break
        else:
            moderator, reason = "Unknown", "No reason"

        embed = discord.Embed(title="⛔ Member banned", color=discord.Color.red())
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="🔧 Banned by", value=f"{moderator} ({moderator.id})" if isinstance(moderator, discord.User) else moderator, inline=False)
        embed.timestamp = discord.utils.utcnow()

        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Logs member unban"""
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.unban):
            if entry.target.id == user.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 10:
                moderator = entry.user
                break
        else:
            moderator = "Unknown"

        embed = discord.Embed(title="✅ Member unbanned", color=discord.Color.green())
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)
        embed.add_field(name="🔧 Unbanned by:", value=f"{moderator} ({moderator.id})" if isinstance(moderator, discord.User) else moderator, inline=False)
        embed.timestamp = discord.utils.utcnow()

        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Logs timeout given/revoked to member"""
        if before.timed_out_until != after.timed_out_until:
            guild = after.guild

            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.member_update):
                if entry.target.id == after.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 10:
                    moderator = entry.user
                    break
            else:
                moderator = "Unknown"

            if after.timed_out_until:
                timeout_until = discord.utils.format_dt(after.timed_out_until, style="F")  # Formatting the date until
                embed = discord.Embed(title="🔇 Member timeouted", color=discord.Color.orange())
                embed.add_field(name="Until", value=timeout_until, inline=False)
            else:
                embed = discord.Embed(title="🔊 Timeout lifted", color=discord.Color.green())

            embed.set_thumbnail(url=after.display_avatar.url)
            embed.add_field(name="User", value=f"{after} ({after.id})", inline=False)
            embed.add_field(name="🔧 Moderator", value=f"{moderator} ({moderator.id})" if isinstance(moderator, discord.User) else moderator, inline=False)
            embed.timestamp = discord.utils.utcnow()

            await self.log_event(embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Logs left/kicked members"""
        guild = member.guild
        joined_at = member.joined_at
        account_creation = member.created_at.strftime("%d/%m/%Y %H:%M:%S")

        # How long member was on the server
        if joined_at:
            duration = discord.utils.utcnow() - member.joined_at
            duration_str = str(duration).split(".")[0]  # Getting rid of milliseconds
            joined_str = joined_at.strftime("%d/%m/%Y, %H:%M:%S")
        else:
            duration_str = "Unknown"
            joined_str = "Unknown"

        # Check the last five entries of audit log for MEMBER_KICK
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 10:
                # If audit log has recent kick -> member was kicked
                embed = discord.Embed(title="⛔ Member Kicked", color=discord.Color.red())
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
                embed.add_field(name="Account Created", value=account_creation, inline=True)
                embed.add_field(name="Moderator", value=f"{entry.user} ({entry.user.id})", inline=False)
                embed.add_field(name="Reason", value=entry.reason if entry.reason else "No reason", inline=False)
                embed.add_field(name="Time on the server", value=f"{duration_str} ({joined_str})", inline=False)
                embed.timestamp = entry.created_at
                await self.log_event(embed)
                return

        # No recent kicks found -> User left
        embed = discord.Embed(title="🚪 User left", color=discord.Color.dark_gray())
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Time on the server", value=f"{duration_str} ({joined_str})", inline=False)
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Logs creation of text, voice channels and categories"""
        guild = channel.guild

        # Checking audit log to get who created channel
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_create):
            if entry.target.id == channel.id:
                creator = entry.user
                break
        else:
            creator = "Unknown"

        channel_type = "Text" if isinstance(channel, discord.TextChannel) else \
            "Voice" if isinstance(channel, discord.VoiceChannel) else \
            "Category"

        embed = discord.Embed(title="📢 Channel created", color=discord.Color.green())
        embed.add_field(name="Name", value=f"{channel.name} ({channel.id})", inline=False)
        embed.add_field(name="Type", value=channel_type, inline=True)
        embed.add_field(name="Creator", value=f"{creator} ({creator.id})" if isinstance(creator, discord.User) else creator, inline=True)
        embed.timestamp = discord.utils.utcnow()

        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Logs channel and category deletion"""
        guild = channel.guild

        # Checking audit log to get who deleted channel
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_delete):
            if entry.target.id == channel.id:
                deleter = entry.user
                break
        else:
            deleter = "Unknown"

        channel_type = "Text" if isinstance(channel, discord.TextChannel) else \
            "Voice" if isinstance(channel, discord.VoiceChannel) else \
            "Category"

        embed = discord.Embed(title="🚫 Channel deleted", color=discord.Color.red())
        embed.add_field(name="Name", value=f"{channel.name} ({channel.id})", inline=False)
        embed.add_field(name="Type", value=channel_type, inline=True)
        embed.add_field(name="Deleter", value=f"{deleter} ({deleter.id})" if isinstance(deleter, discord.User) else deleter, inline=True)
        embed.timestamp = discord.utils.utcnow()

        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_member_roles_update(self, before, after):
        """Logs roles update"""
        guild = before.guild
        added_roles = [role for role in after.roles if role not in before.roles]
        removed_roles = [role for role in before.roles if role not in after.roles]

        if not added_roles and not removed_roles:
            return  # If roles did not change -> exit

        # Check the audit log to get who changed the roles
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.member_role_update):
            if entry.target.id == after.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 10:
                moderator = entry.user
                break
        else:
            moderator = "Unknown"

        embed = discord.Embed(title="🎭 Roles updated", color=discord.Color.blue())
        embed.add_field(name="User", value=f"{after} ({after.id})", inline=False)

        if added_roles:
            embed.add_field(name="✅ Added roles", value=", ".join([role.mention for role in added_roles]),
                            inline=False)

        if removed_roles:
            embed.add_field(name="❌ Deleted roles", value=", ".join([role.mention for role in removed_roles]),
                            inline=False)

        embed.add_field(name="🔧 Changed by", value=f"{moderator} ({moderator.id})" if isinstance(moderator, discord.User) else moderator, inline=False)
        embed.timestamp = discord.utils.utcnow()

        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        """Logs global role perms changes"""
        guild = before.guild

        if before.permissions == after.permissions:
            return  # If perms did not change -> exit

        # Check the audit log to get who changed the perms
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.role_update):
            if entry.target.id == after.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 10:
                moderator = entry.user
                break
        else:
            moderator = "Unknown"

        # Determine updated perms
        added_perms = [perm for perm, value in after.permissions if value and not getattr(before.permissions, perm)]
        removed_perms = [perm for perm, value in before.permissions if value and not getattr(after.permissions, perm)]

        embed = discord.Embed(title="⚙ Role permissions changed globally", color=discord.Color.orange())
        embed.add_field(name="Role", value=f"{after.name} ({after.id})", inline=False)

        if added_perms:
            embed.add_field(name="✅ Added permissions", value=", ".join(added_perms), inline=False)

        if removed_perms:
            embed.add_field(name="❌ Revoked permissions", value=", ".join(removed_perms), inline=False)

        embed.add_field(name="🔧 Changed by", value=f"{moderator} ({moderator.id})" if isinstance(moderator, discord.User) else moderator, inline=False)
        embed.timestamp = discord.utils.utcnow()

        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        """Logs role perms changes in channels or categories"""
        guild = before.guild

        if before.overwrites == after.overwrites:
            return  # If perms did not change -> exit

        # Check the audit log to get who changed the perms
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.overwrite_update):
            if entry.target.id == after.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 10:
                moderator = entry.user
                break
        else:
            moderator = "Unknown"

        embed = discord.Embed(title="🔑 Role permissions changed in channel", color=discord.Color.purple())
        embed.add_field(name="Channel", value=f"{after.name} ({after.id})", inline=False)

        # Determine updated perms
        for target, overwrite in after.overwrites.items():
            if target in before.overwrites:
                before_overwrite = before.overwrites[target]

                added_perms = [perm for perm, value in overwrite if
                               value is True and before_overwrite.get(perm) is not True]
                removed_perms = [perm for perm, value in before_overwrite if
                                 value is True and overwrite.get(perm) is not True]

                if added_perms or removed_perms:
                    embed.add_field(name=f"🔹 Changes for {target.name}", value="\n".join([
                        f"✅ **Added**: {', '.join(added_perms)}" if added_perms else "",
                        f"❌ **Revoked**: {', '.join(removed_perms)}" if removed_perms else "",
                    ]), inline=False)

        embed.add_field(name="🔧 Changed by", value=f"{moderator} ({moderator.id})" if isinstance(moderator, discord.User) else moderator, inline=False)
        embed.timestamp = discord.utils.utcnow()

        await self.log_event(embed)


async def setup(bot):
    await bot.add_cog(AuditLog(bot))
