use poem::{
    handler,
    web::{Data, Json, Path},
};
use serde::Serialize;

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
    db: Data<&sqlx::Pool<sqlx::Postgres>>,
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
