import discord
import random

cpdef tuple handle_message(self: object, m: object, replies: bool):
    if m.author.bot:
        return tuple()

    self.d.msg_count += 1

    if m.content.startswith(f"<@!{self.bot.user.id}>"):
        prefix = self.d.default_prefix

        if m.guild is not None:
            prefix = self.d.prefix_cache.get(m.guild.id, self.d.default_prefix)

        lang = self.bot.get_lang(m)

        embed = discord.Embed(color=self.d.cc, description=lang.misc.pingpong.format(prefix, self.d.support))

        embed.set_author(name="Villager Bot", icon_url=self.d.splash_logo)
        embed.set_footer(text=lang.misc.petus)

        return (m.channel.send(embed=embed),)

    if m.guild is not None:
        if m.guild.id == self.d.support_server_id:
            if m.type in (
                discord.MessageType.premium_guild_subscription,
                discord.MessageType.premium_guild_tier_1,
                discord.MessageType.premium_guild_tier_2,
                discord.MessageType.premium_guild_tier_3,
            ):
                return (
                    self.db.add_item(m.author.id, "Barrel", 1024, 1),
                    self.bot.send(m.author, f"Thanks for boosting the support server! You've received 1x **Barrel**!"),
                )

        content_lowered = m.content.lower()

        if "@someone" in content_lowered:
            someones = [
                u
                for u in m.guild.members
                if (
                    not u.bot
                    and u.status == discord.Status.online
                    and m.author.id != u.id
                    and u.permissions_in(m.channel).read_messages
                )
            ]

            if len(someones) > 0:
                invis = ("||||\u200B" * 200)[2:-3]
                return (m.channel.send(f"@someone {invis} {random.choice(someones).mention} {m.author.mention}"),)
        else:
            if not m.content.startswith(self.d.prefix_cache.get(m.guild.id, self.d.default_prefix)) and replies:
                if "emerald" in content_lowered:
                    return (m.channel.send(random.choice(self.d.hmms)),)
                elif "creeper" in content_lowered:
                    return (m.channel.send("awww{} man".format(random.randint(1, 5) * "w")),)
                elif "reee" in content_lowered:
                    return (m.channel.send(random.choice(self.d.emojis.reees)),)
                elif "amogus" in content_lowered:
                    return (m.channel.send(self.d.emojis.amogus),)

        return tuple()
