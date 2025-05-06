
use chrono::{DateTime, TimeDelta, Utc};
use poem::{
    handler,
    http::StatusCode,
    web::{Data, Json},
};
use serde::{Deserialize, Serialize};

use crate::{
    common::{security::RequireAuthedClient, xid::Xid},
    logic::game::cooldowns::get_or_create_cooldown,
    models::data::commands::CommandsData,
};

#[derive(Deserialize)]
struct CheckCooldownRequest {
    user_id: Xid,
    command: String,
}

#[derive(Debug, Serialize)]
struct CheckCooldownResponse {
    already_on_cooldown: bool,
    cooldown: DateTime<Utc>,
}

#[handler]
pub async fn check_cooldown(
    db: Data<&sqlx::PgPool>,
    commands_data: Data<&CommandsData>,
    data: Json<CheckCooldownRequest>,
    _: RequireAuthedClient,
) -> Result<Json<CheckCooldownResponse>, poem::Error> {
    let Some(cooldown_seconds) = commands_data.cooldowns.get(&data.command) else {
        return Err(poem::Error::from_string(
            format!("Command {:#?} does not have a cooldown", data.command),
            StatusCode::BAD_REQUEST,
        ));
    };

    let default_cooldown = Utc::now() + TimeDelta::seconds(*cooldown_seconds as i64);

    let mut db = db.acquire().await.unwrap();

    let (cooldown, already_on_cooldown) =
        get_or_create_cooldown(&mut db, &data.user_id, &data.command, default_cooldown)
            .await
            .unwrap();

    Ok(Json(CheckCooldownResponse {
        already_on_cooldown,
        cooldown,
    }))
}
