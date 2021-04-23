import sys

# fully reimplemented
import speedups.gateway
import speedups.mixins

# partial implementations
import speedups.activity
import speedups.message


def install():
    discord_module = sys.modules.get("discord")

    # these two were fully reimplemented so just patch em on ez
    discord_module.gateway = speedups.gateway
    discord_module.mixins = speedups.mixins

    for module in (speedups.activity, speedups.message):
        for thing in module.__all__:
            if hasattr(discord_module, thing):
                setattr(discord_module, thing, getattr(module, thing))
