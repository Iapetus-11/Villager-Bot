from typing import Optional

from common.models.base_model import ImmutableBaseModel


class Misc_Errors(ImmutableBaseModel):
    andioop: str
    private: str
    user_perms: str
    bot_perms: str
    concurrency: str
    missing_arg: str
    bad_arg: str
    not_ready: str
    nrn_buddy: str
    disabled: str


class Misc_Time(ImmutableBaseModel):
    day: str
    days: str
    hour: str
    hours: str
    minute: str
    minutes: str
    second: str
    seconds: str


class Misc_Intro(ImmutableBaseModel):
    body: list[str]
    footer: str


class Misc(ImmutableBaseModel):
    pingpong: str
    cooldown_msgs: list[str]
    errors: Misc_Errors
    tips: list[str]
    tip_intros: list[str]
    time: Misc_Time
    intro: Misc_Intro


class Help_Main(ImmutableBaseModel):
    desc: str
    support: str
    clickme: str
    howto: str
    nodoc: str
    aliases: str


class Help_N(ImmutableBaseModel):
    title: str
    economy: str
    minecraft: str
    utility: str
    fun: str
    admin: str
    cmd: str


class Help(ImmutableBaseModel):
    n: Help_N
    main: Help_Main
    econ: dict[str, str]
    mc: dict[str, str]
    util: dict[str, str]
    fun: dict[str, str]
    mod: dict[str, str]


class Fun_Bubblewrap(ImmutableBaseModel):
    invalid_size_1: str
    invalid_size_2: str


class Fun_Trivia_Question(ImmutableBaseModel):
    d: int
    tf: bool
    q: str
    a: list[str]


class Fun_Trivia(ImmutableBaseModel):
    title: str
    title_basic: str
    time_to_answer: str
    timeout: str
    correct: list[str]
    incorrect: list[str]
    difficulty: list[str]
    questions: list[Fun_Trivia_Question]


class Fun(ImmutableBaseModel):
    too_long: str
    dl_img: str
    bubblewrap: Fun_Bubblewrap
    gayrate: str
    trivia: Fun_Trivia


class MobsMech_Lost(ImmutableBaseModel):
    creeper: list[str]
    enderman: list[str]
    normal: list[str]


class MobsMech_Mobs_MobActions(ImmutableBaseModel):
    attacks: list[str]
    finishers: list[str]
    misses: Optional[list[str]] = None


class MobsMech_Mobs(ImmutableBaseModel):
    zombie: MobsMech_Mobs_MobActions
    skeleton: MobsMech_Mobs_MobActions
    spider: MobsMech_Mobs_MobActions
    cave_spider: MobsMech_Mobs_MobActions
    creeper: MobsMech_Mobs_MobActions
    baby_slime: MobsMech_Mobs_MobActions
    enderman: MobsMech_Mobs_MobActions


class MobsMech(ImmutableBaseModel):
    no_health: str
    type_engage: str
    attack_or_flee: str
    flee_insults: list[str]
    user_attacks: list[str]
    user_finishers: list[str]
    mob_drops: list[str]
    found: list[str]
    lost: MobsMech_Lost
    mobs: MobsMech_Mobs


class Minecraft_Mcimage(ImmutableBaseModel):
    stupid_1: str
    stupid_2: str
    stupid_3: str


class Minecraft_Mcping_FieldOnlinePlayers(ImmutableBaseModel):
    name: str
    value: str


class Minecraft_Mcping(ImmutableBaseModel):
    shortcut_error: str
    title_offline: str
    title_online: str
    title_plain: str
    latency: str
    version: str
    field_online_players: Minecraft_Mcping_FieldOnlinePlayers
    and_other_players: str
    learn_more: str
    powered_by: str


class Minecraft_Stealskin(ImmutableBaseModel):
    error: str
    no_skin: str
    embed_desc: str


class Minecraft_Mccolors_FormattingCodes(ImmutableBaseModel):
    red: str
    yellow: str
    green: str
    aqua: str
    blue: str
    light_purple: str
    white: str
    gray: str
    dark_red: str
    gold: str
    dark_green: str
    dark_aqua: str
    dark_blue: str
    dark_purple: str
    dark_gray: str
    black: str
    bold: str
    strikethrough: str
    underline: str
    italic: str
    obfuscated: str
    reset: str


class Minecraft_Mccolors(ImmutableBaseModel):
    embed_desc: str
    embed_author_name: str
    formatting_codes: Minecraft_Mccolors_FormattingCodes
    colors: str
    more_colors: str
    formatting: str


class Minecraft_Rcon(ImmutableBaseModel):
    stupid_1: str
    dm_error: str
    msg_timeout: str
    port: str
    passw: str
    stupid_2: str
    err_con: str
    err_cmd: str


class Minecraft_Profile(ImmutableBaseModel):
    error: str
    first: str
    mcpp: str
    skin: str
    cape: str
    nocape: str
    hist: str


class Minecraft(ImmutableBaseModel):
    invalid_player: str
    mcimage: Minecraft_Mcimage
    mcping: Minecraft_Mcping
    stealskin: Minecraft_Stealskin
    mccolors: Minecraft_Mccolors
    rcon: Minecraft_Rcon
    profile: Minecraft_Profile


class Mod_Purge(ImmutableBaseModel):
    oop: str


class Mod_Kick(ImmutableBaseModel):
    stupid_1: str


class Mod_Ban(ImmutableBaseModel):
    stupid_1: str
    stupid_2: str
    stupid_3: str


class Mod_Unban(ImmutableBaseModel):
    stupid_1: str
    stupid_2: str


class Mod_Warn(ImmutableBaseModel):
    stupid_1: str
    stupid_2: str
    thats_too_much_man: str
    no_reason: str
    by: str
    confirm: str


class Mod_Mute(ImmutableBaseModel):
    stupid_1: str
    stupid_2: str
    stupid_3: str
    mute_msg: str


class Mod_Unmute(ImmutableBaseModel):
    stupid_1: str
    stupid_2: str
    unmute_msg: str


class Mod(ImmutableBaseModel):
    no_perms: str
    purge: Mod_Purge
    kick: Mod_Kick
    ban: Mod_Ban
    unban: Mod_Unban
    warn: Mod_Warn
    mute: Mod_Mute
    unmute: Mod_Unmute


class VbConfig_Main(ImmutableBaseModel):
    title: str
    guild_conf: str
    guild_content: list[str]
    user_conf: str
    user_content: list[str]


class VbConfig_Prefix(ImmutableBaseModel):
    this_server: str
    error_1: str
    error_2: str
    set: str


class VbConfig_Replies(ImmutableBaseModel):
    enabled: str
    disabled: str
    this_server: str
    set: str


class VbConfig_Diff(ImmutableBaseModel):
    this_server: str
    set: str


class VbConfig_Lang(ImmutableBaseModel):
    this_server: str
    set: str


class VbConfig_Mcs(ImmutableBaseModel):
    this_server: str
    error_1: str
    set: str


class VbConfig_Gift(ImmutableBaseModel):
    this_user: str
    set: str


class VbConfig_Cmd(ImmutableBaseModel):
    not_prem: str
    list_cmds: str
    nope: str
    cant: str
    not_found: str
    reenable: str
    disable: str


class VbConfig_Rcon(ImmutableBaseModel):
    none: str
    one: str
    multi: str


class VbConfig(ImmutableBaseModel):

    invalid: str
    main: VbConfig_Main
    prefix: VbConfig_Prefix
    replies: VbConfig_Replies
    diff: VbConfig_Diff
    lang: VbConfig_Lang
    mcs: VbConfig_Mcs
    gift: VbConfig_Gift
    cmd: VbConfig_Cmd
    rcon: VbConfig_Rcon


class Useful_Vote(ImmutableBaseModel):
    click_1: str
    click_2: str


class Useful_Links(ImmutableBaseModel):
    support: str
    invite: str
    topgg: str
    website: str
    source: str
    privacy: str


class Useful_Stats(ImmutableBaseModel):
    stats: str
    servers: str
    dms: str
    users: str
    msgs: str
    cmds: str
    cmds_sec: str
    votes: str
    topgg: str
    shards: str
    ping: str
    mem: str
    cpu: str
    threads: str
    tasks: str
    uptime: str


class Useful_Ginf(ImmutableBaseModel):
    info: str
    age: str
    owner: str
    members: str
    bots: str
    channels: str
    roles: str
    roles_and_n_others: str
    emojis: str
    bans: str
    cmd_prefix: str
    lang: str
    diff: str
    joined_at: str


class Useful_Meth(ImmutableBaseModel):
    oops: str


class Useful_Search(ImmutableBaseModel):
    nope: str
    error: str


class Useful_Rules(ImmutableBaseModel):
    rules: str
    slashrules: str
    penalty: str
    rule_1: str
    rule_2: str
    rule_3: str
    rule_4: str


class Useful_Remind(ImmutableBaseModel):
    reminder_max: str
    stupid_1: str
    time_max: str
    remind: str
    reminder: str


class Useful_Credits(ImmutableBaseModel):
    credits: str
    foot: str
    people: dict[str, str]
    others: str


class Useful_Snipe(ImmutableBaseModel):
    nothing: str


class Useful_Redditdl(ImmutableBaseModel):
    invalid_url: str
    reddit_error: str
    downloading: str
    stitching: str
    couldnt_find: str


class Useful_Imgcmds(ImmutableBaseModel):
    missing: str
    invalid: str
    too_big: str
    error: str


class Useful_Exif(ImmutableBaseModel):
    title: str
    none: str
    discord: str


class Useful_Translate(ImmutableBaseModel):
    stupid_1: str
    stupid_2: str
    stupid_3: str
    error: str


class Useful(ImmutableBaseModel):
    vote: Useful_Vote
    links: Useful_Links
    stats: Useful_Stats
    ginf: Useful_Ginf
    meth: Useful_Meth
    search: Useful_Search
    rules: Useful_Rules
    remind: Useful_Remind
    credits: Useful_Credits
    snipe: Useful_Snipe
    redditdl: Useful_Redditdl
    imgcmds: Useful_Imgcmds
    exif: Useful_Exif
    translate: Useful_Translate


class Econ_MathProblem(ImmutableBaseModel):
    problem: str
    timeout: str
    correct: str
    incorrect: str


class Econ_Pp(ImmutableBaseModel):
    bot_1: str
    bot_2: str
    total_wealth: str
    mooderalds: str
    pick: str
    sword: str
    streak: str
    can_vote: str
    yep: str
    fx: str


class Econ_Bal(ImmutableBaseModel):
    bot_1: str
    bot_2: str
    s_emeralds: str
    total_wealth: str
    autistic_emeralds: str
    pocket: str
    vault: str


class Econ_Inv_Cats(ImmutableBaseModel):
    tools: str
    magic: str
    fish: str
    misc: str
    farming: str
    all: str


class Econ_Inv(ImmutableBaseModel):
    bot_1: str
    bot_2: str
    s_inventory: str
    cats: Econ_Inv_Cats
    empty: str


class Econ_Dep(ImmutableBaseModel):
    poor_loser: str
    stupid_1: str
    stupid_2: str
    stupid_3: str
    deposited: str


class Econ_Withd(ImmutableBaseModel):
    poor_loser: str
    stupid_1: str
    stupid_2: str
    withdrew: str


class Econ_Shop(ImmutableBaseModel):
    villager_shop: str
    tools: str
    magic: str
    farming: str
    other: str
    embed_footer: str


class Econ_Buy(ImmutableBaseModel):
    poor_loser_1: str
    stupid_1: str
    stupid_2: str
    poor_loser_2: str
    need_total_of: str
    you_done_bought: str
    no_to_item_1: str
    no_to_item_2: str


class Econ_Sell(ImmutableBaseModel):
    invalid_item: str
    stupid_1: str
    stupid_2: str
    stupid_3: str
    you_done_sold: str


class Econ_Give(ImmutableBaseModel):
    bot_1: str
    bot_2: str
    stupid_1: str
    stupid_2: str
    and_i_oop: str
    stupid_3: str
    stupid_4: str
    gave: str
    gaveems: str
    gaveyou: str
    gaveyouems: str


class Econ_Gamble(ImmutableBaseModel):
    stupid_1: str
    stupid_2: str
    stupid_3: str
    too_rich: str
    roll: str
    win: str
    lose: str
    tie: str
    actions: list[str]


class Econ_Beg(ImmutableBaseModel):
    positive: list[str]
    negative: list[str]
    mooderald: list[str]


class Econ_Mine(ImmutableBaseModel):
    found_item_1: str
    found_item_2: str
    found_emeralds: str
    actions: list[str]
    places: list[str]
    useless: list[str]


class Econ_Fishing_Market(ImmutableBaseModel):
    title: str
    desc: str
    current: str


class Econ_Fishing(ImmutableBaseModel):
    stupid_1: str
    cast: list[str]
    junk: list[str]
    item: list[str]
    caught: list[str]
    market: Econ_Fishing_Market


class Econ_Pillage_Outcome(ImmutableBaseModel):
    user: list[str]
    victim: list[str]


class Econ_Pillage(ImmutableBaseModel):
    bot_1: str
    bot_2: str
    stupid_1: str
    stupid_2: str
    stupid_3: str
    stupid_4: str
    stupid_5: str
    u_win: Econ_Pillage_Outcome
    u_lose: Econ_Pillage_Outcome


class Econ_Use(ImmutableBaseModel):
    stupid_1: str
    stupid_2: str
    stupid_3: str
    stupid_4: str
    stupid_5: str
    stupid_6: str
    vault_max: str
    vault_pot: str
    smoke_seaweed: str
    use_bonemeal: str
    seaweed_done: str
    chug: str
    chug_no_end: str
    chug_honey: str
    cant_use_any: str
    cant_use_up_to: str
    done: str
    need_slimy_balls: str
    slimy_balls_funne: str
    beaker_of_slime_undo: str
    use_shield_pearl: str
    use_time_pearl: str
    present: list[str]
    barrel_item: list[str]
    barrel_ems: list[str]
    open_item_box: list[str]


class Econ_Farm_Commands(ImmutableBaseModel):
    plant: str
    harvest: str


class Econ_Farm(ImmutableBaseModel):
    s_farm: str
    commands_title: str
    commands: Econ_Farm_Commands
    available: str
    cant_plant: str
    no_plots: str
    no_plots_2: str
    planted: str
    cant_harvest: str
    harvested: str


class Econ_Honey(ImmutableBaseModel):
    stupid_1: list[str]
    honey: list[str]
    ded: list[str]


class Econ_Lb(ImmutableBaseModel):
    title: str
    global_lb: str
    local_lb: str
    emeralds: str
    item: str
    unique_items: str
    stolen: str
    kills: str
    cmds: str
    votes: str
    fish: str
    farming: str
    trash: str
    wems: str
    wcmds: str
    lb_ems: str
    lb_item: str
    lb_unique_items: str
    lb_pil: str
    lb_kil: str
    lb_cmds: str
    lb_votes: str
    lb_fish: str
    lb_farming: str
    lb_trash: str
    lb_wems: str
    lb_wcmds: str
    no_item_lb: str
    item_lb_stats: str


class Econ_Trash(ImmutableBaseModel):
    s_trash: str
    no_trash: str
    total_contents: str
    how_to_empty: str
    emptied_for: str


class Econ(ImmutableBaseModel):
    use_a_number_stupid: str
    page: str
    math_problem: Econ_MathProblem
    pp: Econ_Pp
    bal: Econ_Bal
    inv: Econ_Inv
    dep: Econ_Dep
    withd: Econ_Withd
    shop: Econ_Shop
    buy: Econ_Buy
    sell: Econ_Sell
    give: Econ_Give
    gamble: Econ_Gamble
    beg: Econ_Beg
    mine: Econ_Mine
    fishing: Econ_Fishing
    pillage: Econ_Pillage
    use: Econ_Use
    farm: Econ_Farm
    honey: Econ_Honey
    lb: Econ_Lb
    trash: Econ_Trash


class Translation(ImmutableBaseModel):
    lang: str
    name: str
    misc: Misc
    help: Help
    fun: Fun
    mobs_mech: MobsMech
    minecraft: Minecraft
    mod: Mod
    config: VbConfig
    useful: Useful
    econ: Econ
