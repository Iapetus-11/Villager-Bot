use chrono::{DateTime, TimeDelta, Utc};
use poem::{
    handler,
    http::StatusCode,
    web::{Data, Json},
};
use serde::{Deserialize, Serialize};

use crate::{
    common::{data::COMMANDS_DATA, security::RequireAuthedClient, xid::Xid},
    logic::game::cooldowns::get_or_create_cooldown,
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
    data: Json<CheckCooldownRequest>,
    _: RequireAuthedClient,
) -> Result<Json<CheckCooldownResponse>, poem::Error> {
    let Some(cooldown_seconds) = COMMANDS_DATA.cooldowns.get(&data.command) else {
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

#[cfg(test)]
mod tests {
    use crate::common::testing::{create_test_user, setup_api_test_client};

    use super::*;
    use sqlx::PgPool;

    #[sqlx::test]
    async fn test_check_cooldown(db_pool: PgPool) {
        let mut db = db_pool.acquire().await.unwrap();

        let client = setup_api_test_client(db_pool);

        let user = create_test_user(&mut *db).await;
    }
}