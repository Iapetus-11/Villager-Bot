CREATE TABLE IF NOT EXISTS guilds (
  guild_id           BIGINT PRIMARY KEY, -- the discord guild id / snowflake
  prefix             VARCHAR(15) NOT NULL DEFAULT '!!', -- the prefix of the guild
  difficulty         SMALLINT NOT NULL DEFAULT 1, -- the difficulty the server is on 0=peaceful, 1=normal, 2=hard
  language           VARCHAR(6) NOT NULL DEFAULT 'en', -- the language the bot will speak in
  mc_server          VARCHAR(100), -- the minecraft server of the guild
  premium            BOOLEAN NOT NULL DEFAULT false, -- whether the server is premium or not
  roles_persist      BOOLEAN NOT NULL DEFAULT false -- whether roles should persist or not
);

CREATE TABLE IF NOT EXISTS warnings (
  user_id            BIGINT PRIMARY KEY,  -- the discord user id / snowflake
  guild_id           BIGINT NOT NULL, -- the guild where the user was warned
  mod_id             BIGINT NOT NULL, -- the mod / admin who issued the warning
  reason             VARCHAR(250) -- the reason for the warning (optional)
);

CREATE TABLE IF NOT EXISTS users ( -- used for economy stuff
  user_id            BIGINT PRIMARY KEY,  -- the discord user id / snowflake
  emeralds           BIGINT NOT NULL DEFAULT 0, -- the amount of emeralds the user has
  vault_balance      INT NOT NULL DEFAULT 0, -- the amount of emerald blocks in their vault
  vault_max          INT NOT NULL DEFAULT 1, -- the maximum amount of emerald blocks in their vault
  health             SMALLINT NOT NULL DEFAULT 20, -- the amount of health the user currently has
  vote_streak        INT NOT NULL DEFAULT 0, -- the current vote streak of the user
  last_vote          TIMESTAMPTZ, -- the time at which the last user voted
  give_alert         BOOLEAN NOT NULL DEFAULT true -- whether users should be alerted if someone gives them items or emeralds or not
);

CREATE TABLE IF NOT EXISTS user_bans ( -- if a user exists here, they're bot-banned
  user_id           BIGINT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS items (
  user_id            BIGINT PRIMARY KEY REFERENCES users (user_id) ON DELETE CASCADE, -- the discord user id / snowflake
  name               VARCHAR(50) NOT NULL, -- the name of the item
  sell_price         INT, -- the price it sells back to the bot for
  amount             BIGINT NOT NULL, -- the amount of the item the user has
  sticky             BOOLEAN NOT NULL -- whether the item can be traded / given or not
);

CREATE TABLE IF NOT EXISTS give_logs (
  item               VARCHAR(250) NOT NULL, -- item traded / given, "emerald" for emeralds
  amount             BIGINT NOT NULL, -- the amount of the item
  at                 BIGINT NOT NULL, -- the time at which the transaction was made
  sender             BIGINT NOT NULL, -- who gave the items in the first place
  receiver           BIGINT NOT NULL -- who received the items
);


CREATE TABLE IF NOT EXISTS leaderboards (
  user_id            BIGINT PRIMARY KEY REFERENCES users (user_id) ON DELETE CASCADE, -- the discord user id / snowflake
  pillaged_emeralds  BIGINT NOT NULL DEFAULT 0, -- emeralds pillaged from other users
  mobs_killed        BIGINT NOT NULL DEFAULT 0, -- number of mobs killed
  fish_fished        BIGINT NOT NULL DEFAULT 0  -- fishies fished
);

CREATE TABLE IF NOT EXISTS reminders (
  user_id            BIGINT NOT NULL, -- the discord user id / snowflake
  channel_id         BIGINT NOT NULL, -- the channel id where the reminder command was summoned
  message_id         BIGINT NOT NULL, -- the message where the reminder command was summoned
  reminder           TEXT NOT NULL, -- the actual text for the reminder
  at                 BIGINT NOT NULL -- the time at which the user should be reminded
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

CREATE TABLE IF NOT EXISTS user_roles (
  user_id            BIGINT NOT NULL, -- the discord user id / snowflake
  guild_id           BIGINT NOT NULL, -- the guild id for the user's roles
  roles              BIGINT[] NOT NULL DEFAULT ARRAY[]::BIGINT[] -- the user's roles at the time they left
);
