import speedups.activity as activity
import speedups.gateway as gateway
import speedups.mixins as mixins


def install():
    discord_module = sys.modules.get("discord")

    discord_module.gateway = gateway
    discord_module.mixins = mixins

    discord_module.activity.BaseActivity = activity.BaseActivity
