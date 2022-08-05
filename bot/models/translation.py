from __future__ import annotations
from typing import Optional

from pydantic import BaseModel, Extra


class Misc(BaseModel):
    class Errors(BaseModel):
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

    class Time(BaseModel):
        day: str
        days: str
        hour: str
        hours: str
        minute: str
        minutes: str
        second: str
        seconds: str

    pingpong: str
    cooldown_msgs: list[str]
    errors: Errors
    tips: list[str]
    tip_intros: list[str]
    time: Time


class Help(BaseModel):
    class Main(BaseModel):
        desc: str
        support: str
        clickme: str
        howto: str
        nodoc: str
        aliases: str

    class N(BaseModel):
        title: str
        economy: str
        minecraft: str
        utility: str
        fun: str
        admin: str
        cmd: str

    n: N
    main: Main
    econ: dict[str, str]
    mc: dict[str, str]
    util: dict[str, str]
    fun: dict[str, str]
    mod: dict[str, str]


class Fun(BaseModel):
    class Bubblewrap(BaseModel):
        invalid_size_1: str
        invalid_size_2: str

    class Trivia(BaseModel):
        class Question(BaseModel):
            d: int
            tf: bool
            q: str
            a: list[str]

        title: str
        title_basic: str
        time_to_answer: str
        timeout: str
        correct: list[str]
        incorrect: list[str]
        difficulty: list[str]
        questions: list[Question]

    too_long: str
    dl_img: str
    bubblewrap: Bubblewrap
    gayrate: str
    trivia: Trivia


class MobsMech(BaseModel):
    class Lost(BaseModel):
        creeper: list[str]
        normal: list[str]

    class Mobs(BaseModel):
        class MobActions:
            attacks: list[str]
            finishers: list[str]
            misses: Optional[list[str]] = None

        zombie: MobActions
        skeleton: MobActions
        spider: MobActions
        cave_spider: MobActions
        creeper: MobActions
        baby_slime: MobActions

    no_health: str
    type_engage: str
    attack_or_flee: str
    flee_insults: list[str]
    user_attacks: list[str]
    user_finishers: list[str]
    mob_drops: list[str]
    found: list[str]
    lost: Lost
    mobs: Mobs


class Minecraft(BaseModel):
    class Mcimage(BaseModel):
        stupid_1: str
        stupid_2: str
        stupid_3: str

    class Mcping(BaseModel):
        class FieldOnlinePlayers(BaseModel):
            name: str
            value: str

        shortcut_error: str
        title_offline: str
        title_online: str
        title_plain: str
        latency: str
        version: str
        field_online_players: FieldOnlinePlayers
        and_other_players: str
        learn_more: str
        powered_by: str

    class Stealskin(BaseModel):
        error: str
        no_skin: str
        embed_desc: str

    class Mccolors(BaseModel):
        class FormattingCodes(BaseModel):
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

        embed_desc: str
        embed_author_name: str
        formatting_codes: FormattingCodes
        colors: str
        more_colors: str
        formatting: str

    class Rcon(BaseModel):
        stupid_1: str
        dm_error: str
        msg_timeout: str
        port: str
        passw: str
        stupid_2: str
        err_con: str
        err_cmd: str

    class Profile(BaseModel):
        error: str
        first: str
        mcpp: str
        skin: str
        cape: str
        nocape: str
        hist: str

    invalid_player: str
    mcimage: Mcimage
    mcping: Mcping
    stealskin: Stealskin
    mccolors: Mccolors
    rcon: Rcon
    profile: Profile


class Mod(BaseModel):
    class Purge(BaseModel):
        oop: str

    class Kick(BaseModel):
        stupid_1: str

    class Ban(BaseModel):
        stupid_1: str
        stupid_2: str
        stupid_3: str

    class Unban(BaseModel):
        stupid_1: str
        stupid_2: str

    class Warn(BaseModel):
        stupid_1: str
        stupid_2: str
        thats_too_much_man: str
        no_reason: str
        by: str
        confirm: str

    class Mute(BaseModel):
        stupid_1: str
        stupid_2: str
        stupid_3: str
        mute_msg: str

    class Unmute(BaseModel):
        stupid_1: str
        stupid_2: str
        unmute_msg: str

    no_perms: str
    purge: Purge
    kick: Kick
    ban: Ban
    unban: Unban
    warn: Warn
    mute: Mute
    unmute: Unmute


class VbConfig(BaseModel):
    class Main(BaseModel):
        title: str
        guild_conf: str
        guild_content: list[str]
        user_conf: str
        user_content: list[str]

    class Prefix(BaseModel):
        this_server: str
        error_1: str
        error_2: str
        set: str

    class Replies(BaseModel):
        enabled: str
        disabled: str
        this_server: str
        set: str

    class Diff(BaseModel):
        this_server: str
        set: str

    class Lang(BaseModel):
        this_server: str
        set: str

    class Mcs(BaseModel):
        this_server: str
        error_1: str
        set: str

    class Gift(BaseModel):
        this_user: str
        set: str

    class Cmd(BaseModel):
        not_prem: str
        list_cmds: str
        nope: str
        cant: str
        not_found: str
        reenable: str
        disable: str

    class Rcon(BaseModel):
        none: str
        one: str
        multi: str

    invalid: str
    main: Main
    prefix: Prefix
    replies: Replies
    diff: Diff
    lang: Lang
    mcs: Mcs
    gift: Gift
    cmd: Cmd
    rcon: Rcon


class Useful(BaseModel):
    class Vote(BaseModel):
        click_1: str
        click_2: str

    class Links(BaseModel):
        support: str
        invite: str
        topgg: str
        website: str
        source: str
        privacy: str

    class Stats(BaseModel):
        stats: str
        more: str
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

    class Ginf(BaseModel):
        info: str
        age: str
        owner: str
        members: str
        bots: str
        channels: str
        roles: str
        emojis: str
        bans: str
        cmd_prefix: str
        lang: str
        diff: str

    class Meth(BaseModel):
        oops: str

    class Search(BaseModel):
        nope: str
        error: str

    class Rules(BaseModel):
        rules: str
        slashrules: str
        penalty: str
        rule_1: str
        rule_2: str
        rule_3: str
        rule_4: str

    class Remind(BaseModel):
        reminder_max: str
        stupid_1: str
        time_max: str
        remind: str
        reminder: str

    class Credits(BaseModel):
        credits: str
        foot: str
        people: dict[str, str]
        others: str

    class Snipe(BaseModel):
        nothing: str

    class Redditdl(BaseModel):
        invalid_url: str
        reddit_error: str
        downloading: str
        stitching: str
        couldnt_find: str

    vote: Vote
    links: Links
    stats: Stats
    ginf: Ginf
    meth: Meth
    search: Search
    rules: Rules
    remind: Remind
    credits: Credits
    snipe: Snipe
    redditdl: Redditdl


class Econ(BaseModel):
    class MathProblem(BaseModel):
        problem: str
        timeout: str
        correct: str
        incorrect: str

    class Pp(BaseModel):
        bot_1: str
        bot_2: str
        total_wealth: str
        mooderalds: str
        pick: str
        sword: str
        streak: str
        can_vote: str
        yep: str

    class Bal(BaseModel):
        bot_1: str
        bot_2: str
        s_emeralds: str
        total_wealth: str
        autistic_emeralds: str
        pocket: str
        vault: str

    class Inv(BaseModel):
        class Cats(BaseModel):
            tools: str
            magic: str
            fish: str
            misc: str
            farming: str
            all: str

        bot_1: str
        bot_2: str
        s_inventory: str
        cats: Cats
        empty: str

    class Dep(BaseModel):
        poor_loser: str
        stupid_1: str
        stupid_2: str
        stupid_3: str
        deposited: str

    class Withd(BaseModel):
        poor_loser: str
        stupid_1: str
        stupid_2: str
        withdrew: str

    class Shop(BaseModel):
        villager_shop: str
        tools: str
        magic: str
        farming: str
        other: str
        embed_footer: str

    class Buy(BaseModel):
        poor_loser_1: str
        stupid_1: str
        stupid_2: str
        poor_loser_2: str
        need_total_of: str
        you_done_bought: str
        no_to_item_1: str
        no_to_item_2: str

    class Sell(BaseModel):
        invalid_item: str
        stupid_1: str
        stupid_2: str
        stupid_3: str
        you_done_sold: str

    class Give(BaseModel):
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

    class Gamble(BaseModel):
        stupid_1: str
        stupid_2: str
        stupid_3: str
        too_rich: str
        roll: str
        win: str
        lose: str
        tie: str
        actions: list[str]

    class Beg(BaseModel):
        positive: list[str]
        negative: list[str]
        mooderald: list[str]

    class Mine(BaseModel):
        found_item_1: str
        found_item_2: str
        found_emeralds: str
        actions: list[str]
        places: list[str]
        useless: list[str]

    class Fishing(BaseModel):
        class Market(BaseModel):
            title: str
            desc: str
            current: str

        stupid_1: str
        cast: list[str]
        junk: list[str]
        item: list[str]
        caught: list[str]
        market: Market

    class Pillage(BaseModel):
        class PillageOutcome(BaseModel):
            user: list[str]
            victim: list[str]

        bot_1: str
        bot_2: str
        stupid_1: str
        stupid_2: str
        stupid_3: str
        stupid_4: str
        u_win: PillageOutcome
        u_lose: PillageOutcome

    class Use(BaseModel):
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
        present: list[str]
        barrel_item: list[str]
        barrel_ems: list[str]

    class Farm(BaseModel):
        class FarmCommands(BaseModel):
            plant: str
            harvest: str

        s_farm: str
        commands_title: str
        commands: FarmCommands
        available: str
        cant_plant: str
        no_plots: str
        no_plots_2: str
        planted: str
        cant_harvest: str
        harvested: str

    class Honey(BaseModel):
        stupid_1: list[str]
        honey: list[str]
        ded: list[str]

    class Lb(BaseModel):
        title: str
        global_lb: str
        local_lb: str
        emeralds: str
        stolen: str
        kills: str
        bees: str
        cmds: str
        votes: str
        fish: str
        mooderalds: str
        farming: str
        trash: str
        wems: str
        wcmds: str
        lb_ems: str
        lb_pil: str
        lb_kil: str
        lb_bee: str
        lb_cmds: str
        lb_votes: str
        lb_fish: str
        lb_moods: str
        lb_farming: str
        lb_trash: str
        lb_wems: str
        lb_wcmds: str

    class Trash(BaseModel):
        s_trash: str
        no_trash: str
        total_contents: str
        how_to_empty: str
        emptied_for: str

    use_a_number_stupid: str
    page: str
    math_problem: MathProblem
    pp: Pp
    bal: Bal
    inv: Inv
    dep: Dep
    withd: Withd
    shop: Shop
    buy: Buy
    sell: Sell
    give: Give
    gamble: Gamble
    beg: Beg
    mine: Mine
    fishing: Fishing
    pillage: Pillage
    use: Use
    farm: Farm
    honey: Honey
    lb: Lb
    trash: Trash


class Translation(BaseModel):
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

    class Config:
        validate_all = True
        allow_mutation = False
        extra = Extra.forbid
