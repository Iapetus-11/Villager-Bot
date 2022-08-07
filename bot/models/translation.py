from __future__ import annotations

from typing import Optional

from pydantic import Extra

from common.models.base import ImmutableBaseModel


class Misc(ImmutableBaseModel):
    class Errors(ImmutableBaseModel):
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

    class Time(ImmutableBaseModel):
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


class Help(ImmutableBaseModel):
    class Main(ImmutableBaseModel):
        desc: str
        support: str
        clickme: str
        howto: str
        nodoc: str
        aliases: str

    class N(ImmutableBaseModel):
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


class Fun(ImmutableBaseModel):
    class Bubblewrap(ImmutableBaseModel):
        invalid_size_1: str
        invalid_size_2: str

    class Trivia(ImmutableBaseModel):
        class Question(ImmutableBaseModel):
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


class MobsMech(ImmutableBaseModel):
    class Lost(ImmutableBaseModel):
        creeper: list[str]
        normal: list[str]

    class Mobs(ImmutableBaseModel):
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


class Minecraft(ImmutableBaseModel):
    class Mcimage(ImmutableBaseModel):
        stupid_1: str
        stupid_2: str
        stupid_3: str

    class Mcping(ImmutableBaseModel):
        class FieldOnlinePlayers(ImmutableBaseModel):
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

    class Stealskin(ImmutableBaseModel):
        error: str
        no_skin: str
        embed_desc: str

    class Mccolors(ImmutableBaseModel):
        class FormattingCodes(ImmutableBaseModel):
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

    class Rcon(ImmutableBaseModel):
        stupid_1: str
        dm_error: str
        msg_timeout: str
        port: str
        passw: str
        stupid_2: str
        err_con: str
        err_cmd: str

    class Profile(ImmutableBaseModel):
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


class Mod(ImmutableBaseModel):
    class Purge(ImmutableBaseModel):
        oop: str

    class Kick(ImmutableBaseModel):
        stupid_1: str

    class Ban(ImmutableBaseModel):
        stupid_1: str
        stupid_2: str
        stupid_3: str

    class Unban(ImmutableBaseModel):
        stupid_1: str
        stupid_2: str

    class Warn(ImmutableBaseModel):
        stupid_1: str
        stupid_2: str
        thats_too_much_man: str
        no_reason: str
        by: str
        confirm: str

    class Mute(ImmutableBaseModel):
        stupid_1: str
        stupid_2: str
        stupid_3: str
        mute_msg: str

    class Unmute(ImmutableBaseModel):
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


class VbConfig(ImmutableBaseModel):
    class Main(ImmutableBaseModel):
        title: str
        guild_conf: str
        guild_content: list[str]
        user_conf: str
        user_content: list[str]

    class Prefix(ImmutableBaseModel):
        this_server: str
        error_1: str
        error_2: str
        set: str

    class Replies(ImmutableBaseModel):
        enabled: str
        disabled: str
        this_server: str
        set: str

    class Diff(ImmutableBaseModel):
        this_server: str
        set: str

    class Lang(ImmutableBaseModel):
        this_server: str
        set: str

    class Mcs(ImmutableBaseModel):
        this_server: str
        error_1: str
        set: str

    class Gift(ImmutableBaseModel):
        this_user: str
        set: str

    class Cmd(ImmutableBaseModel):
        not_prem: str
        list_cmds: str
        nope: str
        cant: str
        not_found: str
        reenable: str
        disable: str

    class Rcon(ImmutableBaseModel):
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


class Useful(ImmutableBaseModel):
    class Vote(ImmutableBaseModel):
        click_1: str
        click_2: str

    class Links(ImmutableBaseModel):
        support: str
        invite: str
        topgg: str
        website: str
        source: str
        privacy: str

    class Stats(ImmutableBaseModel):
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

    class Ginf(ImmutableBaseModel):
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

    class Meth(ImmutableBaseModel):
        oops: str

    class Search(ImmutableBaseModel):
        nope: str
        error: str

    class Rules(ImmutableBaseModel):
        rules: str
        slashrules: str
        penalty: str
        rule_1: str
        rule_2: str
        rule_3: str
        rule_4: str

    class Remind(ImmutableBaseModel):
        reminder_max: str
        stupid_1: str
        time_max: str
        remind: str
        reminder: str

    class Credits(ImmutableBaseModel):
        credits: str
        foot: str
        people: dict[str, str]
        others: str

    class Snipe(ImmutableBaseModel):
        nothing: str

    class Redditdl(ImmutableBaseModel):
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


class Econ(ImmutableBaseModel):
    class MathProblem(ImmutableBaseModel):
        problem: str
        timeout: str
        correct: str
        incorrect: str

    class Pp(ImmutableBaseModel):
        bot_1: str
        bot_2: str
        total_wealth: str
        mooderalds: str
        pick: str
        sword: str
        streak: str
        can_vote: str
        yep: str

    class Bal(ImmutableBaseModel):
        bot_1: str
        bot_2: str
        s_emeralds: str
        total_wealth: str
        autistic_emeralds: str
        pocket: str
        vault: str

    class Inv(ImmutableBaseModel):
        class Cats(ImmutableBaseModel):
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

    class Dep(ImmutableBaseModel):
        poor_loser: str
        stupid_1: str
        stupid_2: str
        stupid_3: str
        deposited: str

    class Withd(ImmutableBaseModel):
        poor_loser: str
        stupid_1: str
        stupid_2: str
        withdrew: str

    class Shop(ImmutableBaseModel):
        villager_shop: str
        tools: str
        magic: str
        farming: str
        other: str
        embed_footer: str

    class Buy(ImmutableBaseModel):
        poor_loser_1: str
        stupid_1: str
        stupid_2: str
        poor_loser_2: str
        need_total_of: str
        you_done_bought: str
        no_to_item_1: str
        no_to_item_2: str

    class Sell(ImmutableBaseModel):
        invalid_item: str
        stupid_1: str
        stupid_2: str
        stupid_3: str
        you_done_sold: str

    class Give(ImmutableBaseModel):
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

    class Gamble(ImmutableBaseModel):
        stupid_1: str
        stupid_2: str
        stupid_3: str
        too_rich: str
        roll: str
        win: str
        lose: str
        tie: str
        actions: list[str]

    class Beg(ImmutableBaseModel):
        positive: list[str]
        negative: list[str]
        mooderald: list[str]

    class Mine(ImmutableBaseModel):
        found_item_1: str
        found_item_2: str
        found_emeralds: str
        actions: list[str]
        places: list[str]
        useless: list[str]

    class Fishing(ImmutableBaseModel):
        class Market(ImmutableBaseModel):
            title: str
            desc: str
            current: str

        stupid_1: str
        cast: list[str]
        junk: list[str]
        item: list[str]
        caught: list[str]
        market: Market

    class Pillage(ImmutableBaseModel):
        class PillageOutcome(ImmutableBaseModel):
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

    class Use(ImmutableBaseModel):
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

    class Farm(ImmutableBaseModel):
        class FarmCommands(ImmutableBaseModel):
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

    class Honey(ImmutableBaseModel):
        stupid_1: list[str]
        honey: list[str]
        ded: list[str]

    class Lb(ImmutableBaseModel):
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

    class Trash(ImmutableBaseModel):
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
