use chrono::{DateTime, SubsecRound, TimeDelta, Utc};
use sqlx::PgConnection;

use crate::{
    common::xid::Xid,
    models::db::{DiscordGuild, User},
};
pub type PgPoolConn = sqlx::pool::PoolConnection<sqlx::Postgres>;

pub struct CreateTestUser {
    pub id: Xid,
    pub discord_id: Option<i64>,
    pub banned: bool,
    pub emeralds: i64,
    pub vault_balance: i32,
    pub vault_max: i32,
    pub health: i16,
    pub vote_streak: i32,
    pub last_vote_at: Option<DateTime<Utc>>,
    pub give_alert: bool,
    pub shield_pearl_activated_at: Option<DateTime<Utc>>,
    pub last_daily_quest_reroll: Option<DateTime<Utc>>,
    pub modified_at: DateTime<Utc>,
}

impl Default for CreateTestUser {
    fn default() -> Self {
        let now = Utc::now().trunc_subsecs(6);
        let ten_seconds_ago = now - TimeDelta::seconds(10);
        let two_hours_ago = now - TimeDelta::hours(2);
        let five_days_ago = now - TimeDelta::days(5);

        Self {
            id: Xid::new(),
            discord_id: Some(536986067140608041),
            banned: true,
            emeralds: 420,
            vault_balance: 69,
            vault_max: 666,
            health: 19,
            vote_streak: 2,
            last_vote_at: Some(ten_seconds_ago),
            give_alert: false,
            shield_pearl_activated_at: Some(two_hours_ago),
            last_daily_quest_reroll: Some(five_days_ago),
            modified_at: now,
        }
    }
}

pub async fn create_test_user(db: &mut PgConnection, create_options: CreateTestUser) -> User {
    let user = User {
        id: create_options.id,
        discord_id: create_options.discord_id,
        banned: create_options.banned,
        emeralds: create_options.emeralds,
        vault_balance: create_options.vault_balance,
        vault_max: create_options.vault_max,
        health: create_options.health,
        vote_streak: create_options.vote_streak,
        last_vote_at: create_options.last_vote_at,
        give_alert: create_options.give_alert,
        shield_pearl_activated_at: create_options.shield_pearl_activated_at,
        last_daily_quest_reroll: create_options.last_daily_quest_reroll,
        modified_at: create_options.modified_at,
    };

    sqlx::query!(
        r#"
            INSERT INTO users (
                id, discord_id, banned, emeralds, vault_balance, vault_max, health, vote_streak, last_vote_at,
                give_alert, shield_pearl_activated_at, last_daily_quest_reroll, modified_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        "#,
        user.id.as_bytes(),
        user.discord_id,
        user.banned,
        user.emeralds,
        user.vault_balance,
        user.vault_max,
        user.health,
        user.vote_streak,
        user.last_vote_at,
        user.give_alert,
        user.shield_pearl_activated_at,
        user.last_daily_quest_reroll,
        user.modified_at,
    ).execute(&mut *db).await.unwrap();

    user
}

pub struct CreateTestDiscordGuild {
    pub id: i64,
    pub prefix: String,
    pub language: String,
    pub mc_server: Option<String>,
    pub silly_triggers: bool,
    pub disabled_commands: Vec<String>,
}

impl Default for CreateTestDiscordGuild {
    fn default() -> Self {
        Self {
            id: 641117791272960031,
            prefix: "!!".to_string(),
            language: "en".to_string(),
            mc_server: Some("xenon.devilsquares.me".to_string()),
            silly_triggers: true,
            disabled_commands: vec!["pillage".to_string()],
        }
    }
}

pub async fn create_test_discord_guild(
    db: &mut PgConnection,
    create_options: CreateTestDiscordGuild,
) -> DiscordGuild {
    let discord_guild = DiscordGuild {
        id: create_options.id,
        prefix: create_options.prefix,
        language: create_options.language,
        mc_server: create_options.mc_server,
        silly_triggers: create_options.silly_triggers,
        disabled_commands: create_options.disabled_commands,
    };

    sqlx::query!(
        r#"
            INSERT INTO discord_guilds (
                id, prefix, language, mc_server, silly_triggers, disabled_commands
            ) VALUES ($1, $2, $3, $4, $5, $6)
        "#,
        discord_guild.id,
        discord_guild.prefix,
        discord_guild.language,
        discord_guild.mc_server,
        discord_guild.silly_triggers,
        &discord_guild.disabled_commands,
    )
    .execute(&mut *db)
    .await
    .unwrap();

    discord_guild
}
