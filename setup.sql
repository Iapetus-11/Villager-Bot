CREATE TABLE IF NOT EXISTS guilds (
  gid            BIGINT, -- guild id
  prefix         VARCHAR(15), -- prefix in that server
  replies        BOOL, -- whether or not the should reply to "emeralds" and "villager bot"
  difficulty     VARCHAR(15), -- difficulty for mob spawns and other things
  lang           VARCHAR(10), -- language used leave null for en-us
  mcserver       VARCHAR(50), -- default mcserver for the /mcstatus command
  premium        BOOL
);

CREATE TABLE IF NOT EXISTS users (
  uid           BIGINT, -- user id
  emeralds      BIGINT, -- amount of emeralds user has outside of the vault
  vault_bal     INT, -- amount of emerald BLOCKS which are currently in the vault
  vault_max     INT, -- maximum amount of emerald BLOCKS which can be stored in the vault
  health        INT, -- user health, out of 20
  bot_banned    BOOL, -- is banned from using the bot
  vote_streak   INT,
  streak_time   BIGINT,
  give_alert    BOOL -- whether to tell user if someone gave em stuff or not
);

CREATE TABLE IF NOT EXISTS items (
  uid          BIGINT, -- owner of the item
  name         VARCHAR(250), -- name of the item
  sell_price   BIGINT, -- sell price for ONE of that item
  amount       BIGINT,  -- amount of the item
  sticky       BOOL -- if true, item can't be traded
);

CREATE TABLE IF NOT EXISTS give_logs (
  item       VARCHAR(250),
  amount     BIGINT,
  ts         BIGINT,
  giver_uid  BIGINT,
  recvr_uid  BIGINT
);

CREATE TABLE IF NOT EXISTS leaderboards ( -- there are more leaderboards than this, not all of them are stored here
  uid          BIGINT,
  pillages     BIGINT, -- number of pillaged emeralds
  mobs_killed  BIGINT
);

CREATE TABLE IF NOT EXISTS warnings ( -- moderation warnings
  uid    BIGINT, -- receiver of the warning
  gid    BIGINT, -- guild in which the warning was done
  mod_id BIGINT, -- moderator who did the warning
  reason VARCHAR(250) -- reason for the warning, null for no reason
);

CREATE TABLE IF NOT EXISTS mcservers ( -- used in /randommc command
  owner_id BIGINT, -- discord owner id of the server
  host     VARCHAR(100), -- hostname/ip/address of server
  link     VARCHAR(250) -- learn more link
);

CREATE TABLE IF NOT EXISTS disabled (
  gid BIGINT,
  cmd VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS user_rcon (
  uid       BIGINT,
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
