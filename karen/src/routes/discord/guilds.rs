use poem::{
    handler,
    web::{Data, Json, Path},
};
use serde::Serialize;

use crate::{
    common::security::RequireAuthedClient, logic::discord_guilds::get_or_create_discord_guild,
    models::DiscordGuild,
};

#[derive(Serialize)]
struct GuildDetailsView {
    id: i64,
    prefix: String,
    language: String,
    mc_server: Option<String>,
    silly_triggers: bool,
}

impl From<DiscordGuild> for GuildDetailsView {
    fn from(value: DiscordGuild) -> Self {
        Self {
            id: value.id,
            prefix: value.prefix,
            language: value.language,
            mc_server: value.mc_server,
            silly_triggers: value.silly_triggers,
        }
    }
}

#[handler]
pub async fn get_guild_details(
    db: Data<&sqlx::Pool<sqlx::Postgres>>,
    Path((guild_id,)): Path<(u64,)>,
    _: RequireAuthedClient,
) -> poem::Result<Json<GuildDetailsView>> {
    let guild_id = guild_id as i64;

    let discord_guild = get_or_create_discord_guild(*db, guild_id).await.unwrap();

    Ok(Json(GuildDetailsView::from(discord_guild)))
}
