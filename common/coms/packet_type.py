from enum import IntEnum, auto


class PacketType(IntEnum):
    # special packet types handled directly by the Server/Client classes
    AUTH = auto()
    BROADCAST_REQUEST = auto()
    
    # other regular packet types
    CLUSTER_READY = auto()
    EXEC = auto()
    COOLDOWN = auto()
    COOLDOWN_ADD = auto()
    COOLDOWN_RESET = auto()
    DM_MESSAGE = auto()
    DM_MESSAGE_REQUEST = auto()
    MINE_COMMAND = auto()
    MINE_COMMANDS_RESET = auto()
    CONCURRENCY_CHECK = auto()
    CONCURRENCY_ACQUIRE = auto()
    CONCURRENCY_RELEASE = auto()
    COMMAND_RAN = auto()
    ACQUIRE_PILLAGE_LOCK = auto()
    RELEASE_PILLAGE_LOCK = auto()
    PILLAGE = auto()
    REMINDER = auto()
    FETCH_STATS = auto()
    TRIVIA = auto()
    UPDATE_SUPPORT_SERVER_ROLES = auto()
    RELOAD_DATA = auto()
    ECON_PAUSE = auto()
    ECON_PAUSE_UNDO = auto()
    ECON_PAUSE_CHECK = auto()
    ACTIVE_FX_CHECK = auto()
    ACTIVE_FX_ADD = auto()
    ACTIVE_FX_REMOVE = auto()
    ACTIVE_FX_FETCH = auto()
