CREATE TABLE IF NOT EXISTS server_configs(
  gid        bigint, -- guild id
  prefix     varchar(15), -- prefix in that server
  replies    bool, -- whether or not the should reply to "emeralds" and "villager bot"
  tips       bool, -- whether or not the bot should send a tip occasionally
  difficulty varchar(15) -- difficulty for mob spawns and other things
);

CREATE TABLE IF NOT EXISTS users(
  uid        bigint, -- user id
  emeralds   bigint, -- amount of emeralds user has outside of the vault
  vault_bal  int, -- amount of emerald BLOCKS which are currently in the vault
  vault_max  int, -- maximum amount of emerald BLOCKS which can be stored in the vault
  health     int, -- user health, out of 20
  votes      int, -- total votes on sites like disbots.gg and top.gg
  bot_banned bool -- is banned from using the bot
);

CREATE TABLE IF NOT EXISTS items(
  uid               bigint, -- owner of the item
  item_name         varchar(250), -- name of the item
  sell_price        bigint, -- sell price for ONE of that item
  item_amount       bigint,  -- amount of the item
  original_owner    bigint, -- original owner of the item
  timestamp_created bigint, -- original creation time of the item
  uuid              varchar(128)
);

CREATE TABLE IF NOT EXISTS give_logs(
  item_name             varchar(250),
  amount                bigint,
  transaction_timestamp bigint
);

CREATE TABLE IF NOT EXISTS leaderboards(
  uid             bigint,
  pillages        int, -- number of pillages
  pillages_amount bigint, -- number of pillaged emeralds
  mobs_killed     bigint,
  topgg_votes     int,
  disbots_votes   int
);

CREATE TABLE IF NOT EXISTS warnings( -- moderation warnings
  uid    bigint, -- receiver of the warning
  mod_id bigint, -- moderator who did the warning
  reason varchar(500) -- reason for the warning, null for no reason
);

CREATE TABLE IF NOT EXISTS mc_servers( -- used for the !!randommc command
  owner_id bigint, -- discord user id of the owner
  address  varchar(100), -- address of the server
  port     int, -- port which the server is on
  version  varchar(50), -- Java Edition <version> OR Bedrock Edition
  platform varchar(2), -- either JE or BE
  note     varchar(250) -- optional note
);
