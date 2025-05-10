import discord

from bot.utils.code import format_exception


async def update_support_member_role(bot, member):
    try:
        db = bot.get_cog("Database")

        support_guild = bot.get_guild(bot.k.support_server_id)

        if support_guild is None:
            support_guild = await bot.fetch_guild(bot.k.support_server_id)

        role_map_values = set(bot.d.role_mappings.values())

        roles = []

        for role in member.roles:  # add non rank roles to roles list
            if role.id not in role_map_values and role.id != bot.k.support_server_id:
                roles.append(role)

        pickaxe_role = bot.d.role_mappings.get(await db.fetch_pickaxe(member.id))
        if pickaxe_role is not None:
            roles.append(support_guild.get_role(pickaxe_role))

        if await db.fetch_item(member.id, "Bane Of Pillagers Amulet") is not None:
            roles.append(support_guild.get_role(bot.d.role_mappings.get("BOP")))

        if roles != member.roles:
            try:
                await member.edit(roles=roles)
            except discord.errors.HTTPException:
                pass
    except Exception as e:
        print(format_exception(e))  # noqa: T201
