CREATE TABLE IF NOT EXISTS guilds (
  guild_id           BIGINT PRIMARY KEY, -- the discord guild id / snowflake
  prefix             VARCHAR(15) NOT NULL DEFAULT '!!', -- the prefix of the guild
  difficulty         VARCHAR NOT NULL DEFAULT 'easy', -- the difficulty the server is on peaceful, easy, hard
  language           VARCHAR(6) NOT NULL DEFAULT 'en', -- the language the bot will speak in
  mc_server          VARCHAR(100), -- the minecraft server of the guild
  do_replies         BOOLEAN NOT NULL DEFAULT true, -- whether to do funny replies to certain messages
  antiraid           BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS users ( -- used for economy data
  user_id            BIGINT PRIMARY KEY,  -- the discord user id / snowflake
  bot_banned         BOOLEAN NOT NULL DEFAULT false, -- whether the user is botbanned or not
  emeralds           BIGINT NOT NULL DEFAULT 0, -- the amount of emeralds the user has
  vault_balance      INT NOT NULL DEFAULT 0, -- the amount of emerald blocks in their vault
  vault_max          INT NOT NULL DEFAULT 1, -- the maximum amount of emerald blocks in their vault
  health             SMALLINT NOT NULL DEFAULT 20, -- the amount of health the user currently has
  vote_streak        INT NOT NULL DEFAULT 0, -- the current vote streak of the user
  last_vote          TIMESTAMPTZ, -- the time at which the last user voted
  give_alert         BOOLEAN NOT NULL DEFAULT true -- whether users should be alerted if someone gives them items or emeralds or not
);

CREATE TABLE IF NOT EXISTS items (
  user_id            BIGINT REFERENCES users (user_id) ON DELETE CASCADE, -- the discord user id / snowflake
  name               VARCHAR(50) NOT NULL, -- the name of the item
  sell_price         INT, -- the price it sells back to the bot for
  amount             BIGINT NOT NULL, -- the amount of the item the user has
  sticky             BOOLEAN NOT NULL, -- whether the item can be traded / given or not
  sellable           BOOLEAN NOT NULL -- whether the item can be sold to the bot
);

CREATE TABLE IF NOT EXISTS trash_can (
  user_id            BIGINT REFERENCES users (user_id) ON DELETE CASCADE, -- the discord user id / snowflake
  item               VARCHAR(50) NOT NULL, -- name of item,
  value              FLOAT NOT NULL,
  amount             BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS badges (
  user_id            BIGINT PRIMARY KEY REFERENCES users (user_id) ON DELETE CASCADE,
  code_helper        BOOLEAN NOT NULL DEFAULT false,
  translator         BOOLEAN NOT NULL DEFAULT false,
  design_helper      BOOLEAN NOT NULL DEFAULT false,
  bug_smasher        BOOLEAN NOT NULL DEFAULT false,
  villager_og        BOOLEAN NOT NULL DEFAULT false, -- before the reset
  supporter          BOOLEAN NOT NULL DEFAULT false, -- donated money or bought something from the #paid-stuff channel
  uncle_scrooge      BOOLEAN NOT NULL DEFAULT false, -- given for obtaining more than 100k emeralds
  collector          SMALLINT NOT NULL DEFAULT 0, -- given for collecting items, levels I-V
  beekeeper          SMALLINT NOT NULL DEFAULT 0, -- given for collecting bees, levels I-III
  pillager           SMALLINT NOT NULL DEFAULT 0, -- given for pillaging other users, levels I-III
  murderer           SMALLINT NOT NULL DEFAULT 0, -- given for killing mobs, levels I-III
  enthusiast         SMALLINT NOT NULL DEFAULT 0, -- given for sending many commands, levels I-III
  fisherman          SMALLINT NOT NULL DEFAULT 0 -- given for fishing up fishies, levels I-IV
);

CREATE TABLE IF NOT EXISTS leaderboards (  -- stores leaderboards which aren't stored elsewhere
  user_id            BIGINT PRIMARY KEY REFERENCES users (user_id) ON DELETE CASCADE, -- the discord user id / snowflake
  pillaged_emeralds  BIGINT NOT NULL DEFAULT 0, -- emeralds pillaged from other users
  mobs_killed        BIGINT NOT NULL DEFAULT 0, -- number of mobs killed
  fish_fished        BIGINT NOT NULL DEFAULT 0, -- fishies fished
  commands           BIGINT NOT NULL DEFAULT 0, -- not super accurate as commands are cached for speed
  crops_planted      BIGINT NOT NULL DEFAULT 0,
  trash_emptied      BIGINT NOT NULL DEFAULT 0
);

-- CREATE TABLE IF NOT EXISTS pets (
--   user_id            BIGINT REFERENCES users (user_id) ON DELETE CASCADE,
--   pet_type           VARCHAR(32) NOT NULL,
--   variant            SMALLINT,
--   pet_name           VARCHAR(32),
--   health             SMALLINT NOT NULL, -- 1 point = .5 hearts
--   max_health         SMALLINT NOT NULL, -- max hp
--   hunger             SMALLINT NOT NULL DEFAULT 20, -- 20 hunger points
--   born_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()::TIMESTAMPTZ
-- );

CREATE TABLE IF NOT EXISTS farm_plots (
  user_id            BIGINT REFERENCES users (user_id) ON DELETE CASCADE,
  crop_type          VARCHAR NOT NULL,
  planted_at         TIMESTAMPTZ NOT NULL,
  grow_time          INTERVAL
);

CREATE TABLE IF NOT EXISTS give_logs (
  item               VARCHAR(250) NOT NULL, -- item traded / given, "emerald" for emeralds
  amount             BIGINT NOT NULL, -- the amount of the item
  at                 TIMESTAMPTZ, -- the time at which the transaction was made
  sender             BIGINT NOT NULL, -- who gave the items in the first place
  receiver           BIGINT NOT NULL -- who received the items
);

CREATE TABLE IF NOT EXISTS reminders (
  user_id            BIGINT NOT NULL, -- the discord user id / snowflake
  channel_id         BIGINT NOT NULL, -- the channel id where the reminder command was summoned
  message_id         BIGINT NOT NULL, -- the message where the reminder command was summoned
  reminder           TEXT NOT NULL, -- the actual text for the reminder
  at                 TIMESTAMPTZ -- the time at which the user should be reminded
);

CREATE TABLE IF NOT EXISTS warnings (
  user_id            BIGINT NOT NULL,  -- the discord user id / snowflake
  guild_id           BIGINT NOT NULL, -- the guild where the user was warned
  mod_id             BIGINT NOT NULL, -- the mod / admin who issued the warning
  reason             VARCHAR(250) -- the reason for the warning (optional)
);

CREATE TABLE IF NOT EXISTS disabled_commands (
  guild_id           BIGINT NOT NULL,  -- the guild id where the command is disabled
  command            VARCHAR(20) NOT NULL -- the real name of the command that's disabled
);

CREATE TABLE IF NOT EXISTS user_rcon (
  user_id            BIGINT NOT NULL, -- the discord user id / snowflake
  mc_server          VARCHAR(50) NOT NULL, -- the minecraft server address, including the port
  rcon_port          INT NOT NULL, -- the port the RCON server is hosted on
  password           VARCHAR(300) NOT NULL -- the encrypted password to login to the RCON server
);

CREATE TABLE IF NOT EXISTS filtered_words (
  guild_id           BIGINT NOT NULL,
  word               VARCHAR
);

