----------------------------------------------------------------------------------------------------
-- Make user ID an XID

-- Drop constraints to users table so we can mess up the user_id/id field
ALTER TABLE items DROP CONSTRAINT items_user_id_fkey;
ALTER TABLE trash_can DROP CONSTRAINT trash_can_user_id_fkey;
ALTER TABLE badges DROP CONSTRAINT badges_user_id_fkey;
ALTER TABLE leaderboards DROP CONSTRAINT leaderboards_user_id_fkey;
ALTER TABLE daily_quests DROP CONSTRAINT daily_quests_user_id_fkey;
ALTER TABLE farm_plots DROP CONSTRAINT farm_plots_user_id_fkey;

-- Populate discord_id from user_id
ALTER TABLE users ADD COLUMN discord_id BIGINT UNIQUE;
UPDATE users SET discord_id = user_id;

-- Generates a XID compatible BYTEA value (not a real XID, just good enough and unique)
CREATE OR REPLACE FUNCTION FAKE_XID (snowflake BIGINT)
RETURNS BYTEA
AS $$
	SELECT INT4SEND(1745252807) || INT8SEND(snowflake);
$$ LANGUAGE SQL IMMUTABLE LEAKPROOF PARALLEL SAFE;

-- Technically this should be an XID but that's not built-in to PostgreSQL
ALTER TABLE users ALTER COLUMN user_id TYPE BYTEA USING FAKE_XID(user_id);
ALTER TABLE users RENAME COLUMN user_id TO id;

-- Update tables which have FKs to users + make some field names more consistent
ALTER TABLE items ALTER COLUMN user_id TYPE BYTEA USING FAKE_XID(user_id);
ALTER TABLE items ADD CONSTRAINT items_user_id_fkey FOREIGN KEY (user_id) REFERENCES users (id);
--
ALTER TABLE trash_can ALTER COLUMN user_id TYPE BYTEA USING FAKE_XID(user_id);
ALTER TABLE trash_can ADD CONSTRAINT trash_can_user_id_fkey FOREIGN KEY (user_id) REFERENCES users (id);
--
ALTER TABLE badges ALTER COLUMN user_id TYPE BYTEA USING FAKE_XID(user_id);
ALTER TABLE badges ADD CONSTRAINT badges_user_id_fkey FOREIGN KEY (user_id) REFERENCES users (id);
--
ALTER TABLE leaderboards ALTER COLUMN user_id TYPE BYTEA USING FAKE_XID(user_id);
ALTER TABLE leaderboards ADD CONSTRAINT leaderboards_user_id_fkey FOREIGN KEY (user_id) REFERENCES users (id);
--
ALTER TABLE daily_quests ALTER COLUMN user_id TYPE BYTEA USING FAKE_XID(user_id);
ALTER TABLE daily_quests ADD CONSTRAINT daily_quests_user_id_fkey FOREIGN KEY (user_id) REFERENCES users (id);
--
ALTER TABLE farm_plots ALTER COLUMN user_id TYPE BYTEA USING FAKE_XID(user_id);
ALTER TABLE farm_plots ADD CONSTRAINT farm_plots_user_id_fkey FOREIGN KEY (user_id) REFERENCES users (id);
--
ALTER TABLE give_logs RENAME COLUMN sender TO sender_id;
ALTER TABLE give_logs RENAME COLUMN receiver TO receiver_id;
ALTER TABLE give_logs ALTER COLUMN sender_id TYPE BYTEA USING FAKE_XID(sender_id);
ALTER TABLE give_logs ALTER COLUMN receiver_id TYPE BYTEA USING FAKE_XID(receiver_id);
ALTER TABLE give_logs ADD CONSTRAINT give_logs_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES users (id);
ALTER TABLE give_logs ADD CONSTRAINT give_logs_receiver_id_fkey FOREIGN KEY (receiver_id) REFERENCES users (id);
--
ALTER TABLE command_executions ADD COLUMN discord_user_id BIGINT;
UPDATE command_executions SET discord_user_id = user_id;
ALTER TABLE command_executions ALTER COLUMN discord_user_id SET NOT NULL;
ALTER TABLE command_executions ALTER COLUMN user_id TYPE BYTEA USING FAKE_XID(user_id);
ALTER TABLE command_executions ALTER COLUMN user_id DROP NOT NULL;
UPDATE command_executions SET user_id = (SELECT id FROM users WHERE discord_id = command_executions.discord_user_id);
ALTER TABLE command_executions ADD CONSTRAINT command_executions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users (id);

DROP FUNCTION FAKE_XID;

----------------------------------------------------------------------------------------------------
-- Discord-only table changes

ALTER TABLE reminders RENAME COLUMN user_id TO discord_user_id;
ALTER TABLE reminders RENAME COLUMN channel_id TO discord_channel_id;
ALTER TABLE reminders RENAME COLUMN message_id TO discord_message_id;
ALTER TABLE reminders RENAME COLUMN reminder TO content;

ALTER TABLE warnings RENAME COLUMN guild_id TO discord_guild_id;
ALTER TABLE warnings RENAME COLUMN user_id TO discord_user_id;

ALTER TABLE disabled_commands RENAME COLUMN guild_id TO discord_guild_id;

ALTER TABLE user_rcon RENAME COLUMN user_id TO discord_user_id;

ALTER TABLE guild_events RENAME COLUMN guild_id TO discord_guild_id;

----------------------------------------------------------------------------------------------------
-- Misc changes

ALTER TABLE users RENAME COLUMN bot_banned TO banned;
ALTER TABLE users RENAME COLUMN last_vote TO last_vote_at;
ALTER TABLE users RENAME COLUMN shield_pearl TO shield_pearl_activated_at;
ALTER TABLE users RENAME COLUMN last_dq_reroll TO last_daily_quest_reroll;

ALTER TABLE users ADD COLUMN modified_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

ALTER TABLE guilds RENAME TO discord_guilds;
ALTER TABLE discord_guilds RENAME COLUMN guild_id TO id;
ALTER TABLE discord_guilds RENAME COLUMN do_replies TO silly_triggers;