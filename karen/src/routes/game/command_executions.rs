use chrono::{DateTime, TimeDelta, Utc};
use poem::{
    Body, Response,
    web::{Data, Json},
};
use serde::{Deserialize, Serialize};

use crate::{
    common::{data::COMMANDS_DATA, security::RequireAuthedClient, user_id::UserId, xid::Xid},
    logic::{command_cooldowns::get_or_create_cooldown, command_executions::log_command_execution},
};

#[derive(Debug, Deserialize)]
struct LogCommandExecutionRequest {
    user_id: Xid,
    command: String,
    discord_guild_id: i64,
    is_slash: bool,
    at: DateTime<Utc>,
}

#[derive(Debug, Serialize)]
#[cfg_attr(test, derive(Deserialize))]
struct CommandOnCooldownResponse {
    until: DateTime<Utc>,
}

#[poem::handler]
pub async fn preflight(
    db: Data<&sqlx::PgPool>,
    data: Json<LogCommandExecutionRequest>,
    _: RequireAuthedClient,
) -> Result<(), poem::Error> {
    let mut db = db.acquire().await.unwrap();

    log_command_execution(
        &mut db,
        data.discord_guild_id,
        &data.command,
        data.is_slash,
        data.at,
        &data.user_id,
    )
    .await
    .unwrap();

    if let Some(cooldown_seconds) = COMMANDS_DATA.cooldowns.get(&data.command) {
        // This cooldown will be used if there is no existing cooldown
        let cooldown = data.at + TimeDelta::seconds(*cooldown_seconds as i64);

        let (until, already_on_cooldown) =
            get_or_create_cooldown(&mut db, &data.user_id, &data.command, cooldown)
                .await
                .unwrap();

        if already_on_cooldown {
            return Err(poem::Error::from_response(Response::builder().body(
                Body::from_json(CommandOnCooldownResponse { until }).unwrap(),
            )));
        }
    }

    Ok(())
}
