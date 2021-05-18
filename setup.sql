CREATE TABLE IF NOT EXISTS guilds (
  guild_id        BIGINT PRIMARY KEY, -- the discord guild id / snowflake
  prefix          VARCHAR(15) NOT NULL DEFAULT '!!', -- the prefix of the guild
  difficulty      SMALLINT NOT NULL DEFAULT 1, -- the difficulty the server is on 0=peaceful, 1=normal, 2=hard
  lang            VARCHAR(6) NOT NULL DEFAULT 'en', -- the language
  mc_server       VARCHAR(100),
  premium         BOOLEAN NOT NULL DEFAULT false,
  roles_persist   BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS warnings (
  user_id         BIGINT PRIMARY KEY,  -- the discord user id / snowflake
  guild_id        BIGINT NOT NULL, -- the guild where the user was warned
  mod_id          BIGINT NOT NULL, -- the mod / admin who issued the warning
  reason          VARCHAR(250) -- the reason for the warning (optional)
);

CREATE TABLE IF NOT EXISTS users (
  user_id         BIGINT PRIMARY KEY,  -- the discord user id / snowflake
  emeralds        BIGINT NOT NULL DEFAULT 0,
  vault_balance   INT NOT NULL DEFAULT 0,
  vault_max       INT NOT NULL DEFAULT 1,
  health          SMALLINT NOT NULL DEFAULT 20,
  banned          BOOLEAN NOT NULL DEFAULT false,
  vote_streak     INT NOT NULL DEFAULT 0,
  last_vote       TIMESTAMPTZ,
  give_alert      BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS items (
  user_id         BIGINT PRIMARY KEY REFERENCES users (user_id) ON DELETE CASCADE,  -- the discord user id / snowflake
  name            VARCHAR(50) NOT NULL, -- the name of the item
  sell_price      INT, -- the price it sells back to the bot for
  amount          BIGINT NOT NULL, -- the amount of the item the user has
  sticky          BOOLEAN NOT NULL -- whether the item can be traded / given or not
);
