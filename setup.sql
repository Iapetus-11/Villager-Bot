-- stores guild configuration
CREATE TABLE IF NOT EXISTS guilds (
  gid            BIGINT PRIMARY KEY NOT NULL, -- guild id
  prefix         VARCHAR(15) NOT NULL, -- prefix in that server
  replies        BOOLEAN NOT NULL, -- whether or not the should reply to "emeralds" and "villager bot"
  difficulty     VARCHAR(15) NOT NULL, -- difficulty for mob spawns and other things
  lang           VARCHAR(10) NOT NULL, -- language used leave null for en-us
  mcserver       VARCHAR(50), -- default mcserver for the /mcstatus command
  premium        BOOLEAN
);

-- a user's economy data
CREATE TABLE IF NOT EXISTS users (
  uid           BIGINT PRIMARY KEY NOT NULL, -- user id
  emeralds      BIGINT NOT NULL, -- amount of emeralds user has outside of the vault
  vault_bal     INT NOT NULL, -- amount of emerald BLOCKS which are currently in the vault
  vault_max     INT NOT NULL, -- maximum amount of emerald BLOCKS which can be stored in the vault
  health        INT NOT NULL, -- user health, out of 20
  bot_banned    BOOLEAN NOT NULL, -- is banned from using the bot
  vote_streak   INT NOT NULL,
  streak_time   BIGINT,
  give_alert    BOOLEAN NOT NULL -- whether to tell user if someone gave em stuff or not
);

-- tracks user's items
CREATE TABLE IF NOT EXISTS items (
  uid          BIGINT NOT NULL, -- owner of the item
  name         VARCHAR(250) NOT NULL, -- name of the item
  sell_price   BIGINT, -- sell price for ONE of that item
  amount       BIGINT NOT NULL,  -- amount of the item
  sticky       BOOLEAN NOT NULL -- if true, item can't be traded
);

-- tracks economy transactions between users
CREATE TABLE IF NOT EXISTS give_logs (
  item       VARCHAR(250) NOT NULL,
  amount     BIGINT NOT NULL,
  ts         BIGINT NOT NULL,
  giver_uid  BIGINT NOT NULL,
  recvr_uid  BIGINT NOT NULL
);

-- used for leaderboards as part of the economy suite
CREATE TABLE IF NOT EXISTS leaderboards ( -- there are more leaderboards than this, not all of them are stored here
  uid          BIGINT PRIMARY KEY NOT NULL,
  pillages     BIGINT NOT NULL, -- number of pillaged emeralds
  mobs_killed  BIGINT NOT NULL,
  fish         BIGINT NOT NULL -- number of fish fished up
);

-- used for warning system as part of moderation suite
CREATE TABLE IF NOT EXISTS warnings (
  uid    BIGINT NOT NULL, -- receiver of the warning
  gid    BIGINT NOT NULL, -- guild in which the warning was done
  mod_id BIGINT NOT NULL, -- moderator who did the warning
  reason VARCHAR(250) -- reason for the warning, null for no reason
);

-- used in !!randommc command
CREATE TABLE IF NOT EXISTS mcservers (
  owner_id BIGINT NOT NULL, -- discord owner id of the server
  host     VARCHAR(100), -- hostname/ip/address of server
  link     VARCHAR(250) -- learn more link
);

-- used to store disabled commands for premium servers
CREATE TABLE IF NOT EXISTS disabled (
  gid BIGINT NOT NULL,
  cmd VARCHAR(20) NOT NULL
);

-- used to store connection credentials + info for rcon command
CREATE TABLE IF NOT EXISTS user_rcon (
  uid       BIGINT NOT NULL,
  mcserver  VARCHAR(50),
  rcon_port INT,
  password  VARCHAR(300)
);

-- used for reminders command
CREATE TABLE IF NOT EXISTS reminders (
  uid BIGINT NOT NULL,
  cid BIGINT NOT NULL,
  mid BIGINT NOT NULL,
  reminder VARCHAR(500),
  at BIGINT NOT NULL
);

-- used to store roles of users in guilds with role persistence on
CREATE TABLE IF NOT EXISTS user_roles (
  uid BIGINT NOT NULL,
  gid BIGINT NOT NULL,
  roles BIGINT[] NOT NULL DEFAULT {}
);
