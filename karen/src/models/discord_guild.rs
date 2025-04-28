use serde::Serialize;
use sqlx::FromRow;

#[derive(Debug, FromRow, Serialize)]
pub struct DiscordGuild {
    pub id: i64,
    pub prefix: String,
    pub language: String,
    pub mc_server: Option<String>,
    pub silly_triggers: bool,
}
