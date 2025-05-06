use chrono::{DateTime, Utc};
use poem::{
    handler,
    web::{Data, Json},
};
use serde::{Deserialize, Serialize};

use crate::{
    common::{security::RequireAuthedClient, xid::Xid},
    logic::game::cooldowns::get_cooldown,
};

#[derive(Deserialize)]
struct CheckCooldownRequest {
    user_id: Xid,
    command: String,
}

#[derive(Debug, Serialize)]
struct CheckCooldownResponse {
    cooldown: DateTime<Utc>,
}

#[handler]
pub async fn check_cooldown(
    db: Data<&sqlx::PgPool>,
    data: Json<CheckCooldownRequest>,
    _: RequireAuthedClient,
) -> Result<Json<CheckCooldownResponse>, poem::Error> {
    let mut db = db.acquire().await.unwrap();

    let cooldown = get_cooldown(&mut *db, &data.user_id, &data.command)
        .await
        .unwrap();

    todo!();
}
