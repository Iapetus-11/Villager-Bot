use chrono::{DateTime, Utc};
use poem::{
    handler,
    http::StatusCode,
    web::{Data, Json, Path},
};
use serde::Serialize;

use crate::{
    common::{security::RequireAuthedClient, user_id::UserId, xid::Xid},
    logic::users::{GetOrCreateUserError, get_or_create_user},
    models::db::User,
};

#[derive(Serialize)]
struct UserDetailsView {
    id: Xid,
    discord_id: Option<i64>,
    banned: bool,
    emeralds: i64,
    vault_balance: i32,
    vault_max: i32,
    health: i16,
    vote_streak: i32,
    last_vote_at: Option<DateTime<Utc>>,
    give_alert: bool,
    shield_pearl_activated_at: Option<DateTime<Utc>>,
    last_daily_quest_reroll: Option<DateTime<Utc>>,
    modified_at: DateTime<Utc>,
}

impl From<User> for UserDetailsView {
    fn from(value: User) -> Self {
        UserDetailsView {
            id: value.id,
            discord_id: value.discord_id,
            banned: value.banned,
            emeralds: value.emeralds,
            vault_balance: value.vault_balance,
            vault_max: value.vault_max,
            health: value.health,
            vote_streak: value.vote_streak,
            last_vote_at: value.last_vote_at,
            give_alert: value.give_alert,
            shield_pearl_activated_at: value.shield_pearl_activated_at,
            last_daily_quest_reroll: value.last_daily_quest_reroll,
            modified_at: value.modified_at,
        }
    }
}

#[handler]
pub async fn get_user_details(
    db: Data<&sqlx::PgPool>,
    Path((user_id,)): Path<(UserId,)>,
    _: RequireAuthedClient,
) -> poem::Result<Json<UserDetailsView>> {
    let mut db = db.acquire().await.unwrap();

    let user_result = get_or_create_user(&mut db, &user_id).await;

    if matches!(user_result, Err(GetOrCreateUserError::CannotCreateUsingXid)) {
        return Err(poem::Error::from_string(
            "User does not exist, and cannot create a new one from an Xid",
            StatusCode::BAD_REQUEST,
        ));
    }

    Ok(Json(UserDetailsView::from(user_result.unwrap())))
}
