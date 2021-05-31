def strip_command(ctx):  # returns message.clean_content excluding the command used
    length = len(ctx.prefix) + len(ctx.invoked_with) + 1
    return ctx.message.clean_content[length:]


def dm_check(ctx):
    def _dm_check(m):
        return ctx.author.id == m.author.id and ctx.author.dm_channel.id == m.channel.id

    return _dm_check
