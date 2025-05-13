----------------------------------------------------------------------------------------------------
-- New stuff

DROP TABLE command_cooldowns;
DROP TABLE user_locks;

----------------------------------------------------------------------------------------------------
-- Misc changes

CREATE TABLE IF NOT EXISTS disabled_commands (
  guild_id           BIGINT NOT NULL,  -- the guild id where the command is disabled
  command            VARCHAR(20) NOT NULL -- the real name of the command that's disabled
);
INSERT INTO disabled_commands SELECT id, UNNEST(disabled_commands) FROM discord_guilds;
ALTER TABLE discord_guilds DROP COLUMN disabled_commands;

ALTER TABLE items DROP CONSTRAINT unique_on_user_and_item;
ALTER TABLE items ALTER COLUMN sell_price DROP NOT NULL;

ALTER TABLE discord_guilds RENAME TO guilds;
ALTER TABLE guilds RENAME COLUMN id TO guild_id;
ALTER TABLE guilds RENAME COLUMN silly_triggers TO do_replies;

ALTER TABLE users DROP COLUMN modified_at;
ALTER TABLE users ALTER COLUMN last_daily_quest_reroll SET NOT NULl;
ALTER TABLE users ALTER COLUMN last_daily_quest_reroll SET DEFAULT NOW();
ALTER TABLE users RENAME COLUMN last_daily_quest_reroll TO last_dq_reroll;
ALTER TABLE users RENAME COLUMN shield_pearl_activated_at TO shield_pearl;
ALTER TABLE users RENAME COLUMN last_vote_at TO last_vote;
ALTER TABLE users RENAME COLUMN banned TO bot_banned;

----------------------------------------------------------------------------------------------------
-- Discord-only table changes

ALTER TABLE guild_events RENAME COLUMN discord_guild_id TO guild_id;

ALTER TABLE user_rcon RENAME COLUMN discord_user_id TO user_id;

ALTER TABLE warnings RENAME COLUMN discord_user_id TO user_id;
ALTER TABLE warnings RENAME COLUMN discord_guild_id TO guild_id;

ALTER TABLE reminders RENAME COLUMN content TO reminder;
ALTER TABLE reminders RENAME COLUMN discord_user_id TO user_id;
ALTER TABLE reminders RENAME COLUMN discord_channel_id TO channel_id;
ALTER TABLE reminders RENAME COLUMN discord_message_id TO message_id;

----------------------------------------------------------------------------------------------------
-- Make user ID not an XID

CREATE OR REPLACE FUNCTION DECODE_BIGINT (b BYTEA)
RETURNS BIGINT
AS $$
	SELECT (
        (GET_BYTE(b, 0)::BIGINT << 56) +
        (GET_BYTE(b, 1)::BIGINT << 48) +
        (GET_BYTE(b, 2)::BIGINT << 40) +
        (GET_BYTE(b, 3)::BIGINT << 32) +
        (GET_BYTE(b, 4)::BIGINT << 24) +
        (GET_BYTE(b, 5)::BIGINT << 16) +
        (GET_BYTE(b, 6)::BIGINT << 8) +
        GET_BYTE(b, 7)::BIGINT
    )
$$ LANGUAGE SQL IMMUTABLE LEAKPROOF PARALLEL SAFE;

CREATE OR REPLACE FUNCTION UNFAKE_XID(id BYTEA)
RETURNS BIGINT
AS $$
    SELECT DECODE_BIGINT(SUBSTRING(id FROM 5 FOR 8))
$$ LANGUAGE SQL IMMUTABLE LEAKPROOF PARALLEL SAFE;

ALTER TABLE command_executions DROP COLUMN user_id;
ALTER TABLE command_executions RENAME COLUMN discord_user_id TO user_id;

ALTER TABLE give_logs DROP CONSTRAINT give_logs_receiver_id_fkey;
ALTER TABLE give_logs DROP CONSTRAINT give_logs_sender_id_fkey;
ALTER TABLE give_logs RENAME COLUMN sender_id TO sender;
ALTER TABLE give_logs RENAME COLUMN receiver_id TO receiver;
ALTER TABLE give_logs ALTER COLUMN sender TYPE BIGINT USING UNFAKE_XID(sender);
ALTER TABLE give_logs ALTER COLUMN receiver TYPE BIGINT USING UNFAKE_XID(receiver);

ALTER TABLE farm_plots DROP CONSTRAINT farm_plots_user_id_fkey;
ALTER TABLE farm_plots ALTER COLUMN user_id TYPE BIGINT USING UNFAKE_XID(user_id);

ALTER TABLE daily_quests DROP CONSTRAINT daily_quests_user_id_fkey;
ALTER TABLE daily_quests ALTER COLUMN user_id TYPE BIGINT USING UNFAKE_XID(user_id);

ALTER TABLE leaderboards DROP CONSTRAINT leaderboards_user_id_fkey;
ALTER TABLE leaderboards ALTER COLUMN user_id TYPE BIGINT USING UNFAKE_XID(user_id);

ALTER TABLE badges DROP CONSTRAINT badges_user_id_fkey;
ALTER TABLE badges ALTER COLUMN user_id TYPE BIGINT USING UNFAKE_XID(user_id);

ALTER TABLE trash_can DROP CONSTRAINT trash_can_user_id_fkey;
ALTER TABLE trash_can ALTER COLUMN user_id TYPE BIGINT USING UNFAKE_XID(user_id);

ALTER TABLE items ALTER COLUMN user_id TYPE BIGINT USING UNFAKE_XID(user_id);

ALTER TABLE users RENAME COLUMN id TO user_id;
ALTER TABLE users ALTER COLUMN user_id TYPE BIGINT USING UNFAKE_XID(user_id);
ALTER TABLE users DROP COLUMN discord_id;

ALTER TABLE farm_plots ADD CONSTRAINT farm_plots_user_id_fkey FOREIGN KEY (user_id) REFERENCES users (user_id);
ALTER TABLE daily_quests ADD CONSTRAINT daily_quests_user_id_fkey FOREIGN KEY (user_id) REFERENCES users (user_id);
ALTER TABLE leaderboards ADD CONSTRAINT leaderboards_user_id_fkey FOREIGN KEY (user_id) REFERENCES users (user_id);
ALTER TABLE badges ADD CONSTRAINT badges_user_id_fkey FOREIGN KEY (user_id) REFERENCES users (user_id);
ALTER TABLE trash_can ADD CONSTRAINT trash_can_user_id_fkey FOREIGN KEY (user_id) REFERENCES users (user_id);
ALTER TABLE items ADD CONSTRAINT items_user_id_fkey FOREIGN KEY (user_id) REFERENCES users (user_id);

DROP FUNCTION UNFAKE_XID;
DROP FUNCTION DECODE_BIGINT;
