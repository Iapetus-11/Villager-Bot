CREATE TABLE IF NOT EXISTS guilds (
  gid            BIGINT PRIMARY KEY NOT NULL, -- guild id
  prefix         VARCHAR(15) NOT NULL, -- prefix in that server
  replies        BOOL NOT NULL, -- whether or not the should reply to "emeralds" and "villager bot"
  difficulty     VARCHAR(15) NOT NULL, -- difficulty for mob spawns and other things
  lang           VARCHAR(10) NOT NULL, -- language used leave null for en-us
  mcserver       VARCHAR(50), -- default mcserver for the /mcstatus command
  premium        BOOL
);

CREATE TABLE IF NOT EXISTS users (
  uid           BIGINT PRIMARY KEY NOT NULL, -- user id
  emeralds      BIGINT NOT NULL, -- amount of emeralds user has outside of the vault
  vault_bal     INT NOT NULL, -- amount of emerald BLOCKS which are currently in the vault
  vault_max     INT NOT NULL, -- maximum amount of emerald BLOCKS which can be stored in the vault
  health        INT NOT NULL, -- user health, out of 20
  bot_banned    BOOL NOT NULL, -- is banned from using the bot
  vote_streak   INT NOT NULL,
  streak_time   BIGINT NOT NULL,
  give_alert    BOOL NOT NULL -- whether to tell user if someone gave em stuff or not
);

CREATE TABLE IF NOT EXISTS items (
  uid          BIGINT PRIMARY KEY NOT NULL, -- owner of the item
  name         VARCHAR(250) NOT NULL, -- name of the item
  sell_price   BIGINT NOT NULL, -- sell price for ONE of that item
  amount       BIGINT NOT NULL,  -- amount of the item
  sticky       BOOL NOT NULL -- if true, item can't be traded
);

CREATE TABLE IF NOT EXISTS give_logs (
  item       VARCHAR(250) NOT NULL,
  amount     BIGINT NOT NULL,
  ts         BIGINT NOT NULL,
  giver_uid  BIGINT NOT NULL,
  recvr_uid  BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS leaderboards ( -- there are more leaderboards than this, not all of them are stored here
  uid          BIGINT PRIMARY KEY NOT NULL,
  pillages     BIGINT NOT NULL, -- number of pillaged emeralds
  mobs_killed  BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS warnings ( -- moderation warnings
  uid    BIGINT PRIMARY KEY NOT NULL, -- receiver of the warning
  gid    BIGINT NOT NULL, -- guild in which the warning was done
  mod_id BIGINT NOT NULL, -- moderator who did the warning
  reason VARCHAR(250) NOT NULL -- reason for the warning, null for no reason
);

CREATE TABLE IF NOT EXISTS mcservers ( -- used in /randommc command
  owner_id BIGINT PRIMARY KEY NOT NULL, -- discord owner id of the server
  host     VARCHAR(100), -- hostname/ip/address of server
  link     VARCHAR(250) -- learn more link
);

CREATE TABLE IF NOT EXISTS disabled (
  gid BIGINT PRIMARY KEY NOT NULL,
  cmd VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS user_rcon (
  uid       BIGINT PRIMARY KEY NOT NULL,
  mcserver  VARCHAR(50),
  rcon_port INT,
  password  VARCHAR(300)
);

-- CREATE TABLE IF NOT EXISTS mc_servers( -- used for the !!randommc command
--   owner_id BIGINT, -- discord user id of the owner
--   address  VARCHAR(100), -- address of the server
--   port     INT, -- port which the server is on
--   version  VARCHAR(50), -- Java Edition <version> OR Bedrock Edition
--   note     VARCHAR(250) -- optional note
-- );
