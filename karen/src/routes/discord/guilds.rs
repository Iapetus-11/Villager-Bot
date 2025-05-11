use poem::{
    handler,
    web::{Data, Json, Path},
};
use serde::{Deserialize, Serialize};

use crate::{
    common::security::RequireAuthedClient, logic::discord_guilds::get_or_create_discord_guild,
    models::db::DiscordGuild,
};

#[derive(Serialize)]
struct GuildDetailsView {
    id: i64,
    prefix: String,
    language: String,
    mc_server: Option<String>,
    silly_triggers: bool,
    disabled_commands: Vec<String>,
}

impl From<DiscordGuild> for GuildDetailsView {
    fn from(value: DiscordGuild) -> Self {
        Self {
            id: value.id,
            prefix: value.prefix,
            language: value.language,
            mc_server: value.mc_server,
            silly_triggers: value.silly_triggers,
            disabled_commands: value.disabled_commands,
        }
    }
}

#[handler]
pub async fn get_guild_details(
    db: Data<&sqlx::PgPool>,
    Path((guild_id,)): Path<(u64,)>,
    _: RequireAuthedClient,
) -> poem::Result<Json<GuildDetailsView>> {
    let mut db = db.acquire().await.unwrap();

    let guild_id = guild_id as i64;

    let discord_guild = get_or_create_discord_guild(&mut db, guild_id)
        .await
        .unwrap();

    Ok(Json(GuildDetailsView::from(discord_guild)))
}

#[derive(Serialize, Deserialize)]
struct UpdateGuildData {
    #[serde(
        default,
        deserialize_with = "crate::common::serde_helpers::deserialize_maybe_undefined",
        skip_serializing_if = "Option::is_none"
    )]
    prefix: Option<Option<String>>,
    #[serde(
        default,
        deserialize_with = "crate::common::serde_helpers::deserialize_maybe_undefined",
        skip_serializing_if = "Option::is_none"
    )]
    language: Option<Option<String>>,
    #[serde(
        default,
        deserialize_with = "crate::common::serde_helpers::deserialize_maybe_undefined",
        skip_serializing_if = "Option::is_none"
    )]
    mc_server: Option<Option<String>>,
    #[serde(
        default,
        deserialize_with = "crate::common::serde_helpers::deserialize_maybe_undefined",
        skip_serializing_if = "Option::is_none"
    )]
    silly_triggers: Option<Option<bool>>,
    #[serde(
        default,
        deserialize_with = "crate::common::serde_helpers::deserialize_maybe_undefined",
        skip_serializing_if = "Option::is_none"
    )]
    disabled_commands: Option<Option<Vec<String>>>,
}

#[handler]
pub async fn update_guild_details(
    db: Data<&sqlx::PgPool>,
    Path((guild_id,)): Path<(i64,)>,
    Json(update_guild_data): Json<UpdateGuildData>,
    _: RequireAuthedClient,
) -> poem::Result<Json<GuildDetailsView>> {
    let mut db = db.acquire().await.unwrap();

    // TODO:
    // 1. Move this to logic layer
    // 2. Add 404 handling

    let updated_guild = sqlx::query_as!(
        DiscordGuild,
        r#"
            UPDATE discord_guilds
            SET
                prefix = CASE WHEN $2 ? 'prefix' THEN ($2->>'prefix')::VARCHAR ELSE prefix END
            WHERE id = $1
            RETURNING id, prefix, language, mc_server, silly_triggers, disabled_commands
        "#,
        guild_id,
        serde_json::to_value(update_guild_data).unwrap(),
    )
    .fetch_one(&mut *db)
    .await
    .unwrap();

    Ok(Json(GuildDetailsView::from(updated_guild)))
}

#[cfg(test)]
mod tests {
    use serde_json::json;
    use sqlx::PgPool;

    use crate::{
        common::testing::{create_test_discord_guild, setup_api_test_client},
        logic::discord_guilds::get_discord_guild,
    };

    use super::*;

    #[sqlx::test]
    async fn test_get_guild_details_of_existing_guild(db_pool: PgPool) {
        let mut db = db_pool.acquire().await.unwrap();

        let discord_guild = create_test_discord_guild(&mut db, Default::default()).await;

        let client = setup_api_test_client(db_pool);
        let response = client
            .get(format!("/discord/guilds/{}", discord_guild.id))
            .send()
            .await;

        response.assert_status_is_ok();
        response
            .assert_json(GuildDetailsView::from(discord_guild))
            .await;
    }

    #[sqlx::test]
    async fn test_get_guild_details_of_nonexistent_guild(db_pool: PgPool) {
        let mut db = db_pool.acquire().await.unwrap();

        let guild_id = 641117791272960031_i64;

        let client = setup_api_test_client(db_pool);
        let response = client
            .get(format!("/discord/guilds/{}", guild_id))
            .send()
            .await;

        let discord_guild = get_discord_guild(&mut db, guild_id).await.unwrap().unwrap();

        response.assert_status_is_ok();
        response
            .assert_json(GuildDetailsView::from(discord_guild))
            .await;
    }

    #[sqlx::test]
    async fn test_update_guild_details(db_pool: PgPool) {
        let mut db = db_pool.acquire().await.unwrap();

        let discord_guild = create_test_discord_guild(&mut db, Default::default()).await;

        let client = setup_api_test_client(db_pool);
        let response = client
            .patch(format!("/discord/guilds/{}", discord_guild.id))
            .body_json(&json!({
                "prefix": "!?"
            }))
            .send()
            .await;

        let updated_discord_guild = get_discord_guild(&mut db, discord_guild.id)
            .await
            .unwrap()
            .unwrap();

        assert_eq!(updated_discord_guild.prefix, "!?");
        assert_ne!(discord_guild.prefix, updated_discord_guild.prefix);
    }
}
