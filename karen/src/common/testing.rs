use std::sync::{Arc, LazyLock, OnceLock};

use chrono::{SubsecRound, TimeDelta, Utc};
use poem::{
    EndpointExt,
    endpoint::BoxEndpoint,
    middleware::{AddData, CatchPanic, NormalizePath, TrailingSlash},
    test::TestClient,
};
use sqlx::PgConnection;

use crate::{
    config::Config,
    models::db::{DiscordGuild, User},
    routes,
};

use super::xid::Xid;

pub type PgPoolConn = sqlx::pool::PoolConnection<sqlx::Postgres>;

pub async fn create_test_user(db: &mut PgConnection) -> User {
    let user_id = Xid::new();

    // Truncate subsecs because for some reason the precision is weird on windows postgresql?
    let now = Utc::now().trunc_subsecs(6);
    let ten_seconds_ago = now - TimeDelta::seconds(10);
    let two_hours_ago = now - TimeDelta::hours(2);
    let five_days_ago = now - TimeDelta::days(5);

    let user = User {
        id: user_id,
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

pub struct TestDiscordGuild {
    pub id: i64,
    pub prefix: String,
    pub language: String,
    pub mc_server: Option<String>,
    pub silly_triggers: bool,
    pub disabled_commands: Vec<String>,
}

impl Default for TestDiscordGuild {
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
    create_options: TestDiscordGuild,
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

pub static TEST_CONFIG: LazyLock<Config> = LazyLock::new(|| Config {
    database_url: "postgresql://test_user:password@example.com/villager-bot".to_string(),
    database_pool_size: 0,
    server_host_address: "http://127.0.0.1:-1".to_string(),
    auth_token: "auth token".to_string(),
});

// Cache API test client to improve test execution speed
static TEST_API_INSTANCE: OnceLock<Arc<BoxEndpoint<'static>>> = OnceLock::new();

pub fn setup_api_test_client(db_pool: sqlx::PgPool) -> TestClient<BoxEndpoint<'static>> {
    let cached_app = TEST_API_INSTANCE.get_or_init(|| {
        let config = Config {
            database_url: "postgresql://test_user:password@example.com/villager-bot".to_string(),
            database_pool_size: 0,
            server_host_address: "http://127.0.0.1:-1".to_string(),
            auth_token: "auth token".to_string(),
        };

        let app = routes::setup_routes()
            .with(NormalizePath::new(TrailingSlash::Always))
            .with(AddData::new(config))
            .with(CatchPanic::new());

        Arc::new(app.boxed())
    });

    // I do not know exactly what #[sqlx::test] does under the hood, specifically if they reuse db pools between tests,
    // either way I want to be safe.
    TestClient::new(cached_app.clone().with(AddData::new(db_pool)).boxed())
}
