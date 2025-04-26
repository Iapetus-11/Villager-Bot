use chrono::{DateTime, Utc};
use poem::{
    error::NotFoundError,
    handler,
    http::StatusCode,
    web::{Data, Json, Path},
};
use serde::Serialize;

use crate::{
    common::{security::RequireAuthedClient, user_id::UserId, xid::Xid},
    models::User,
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
    last_daily_quest_reroll: DateTime<Utc>,
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
        }
    }
}

#[handler]
pub async fn get_user_details(
    db: Data<&sqlx::Pool<sqlx::Postgres>>,
    Path((user_id,)): Path<(UserId,)>,
    _: RequireAuthedClient,
) -> poem::Result<Json<UserDetailsView>> {
    let user = match user_id {
        UserId::Xid(xid) => sqlx::query_as!(
            User,
            r#"
                SELECT
                    id, discord_id, banned, emeralds, vault_balance, vault_max, health, vote_streak, last_vote_at,
                    give_alert, shield_pearl_activated_at, last_daily_quest_reroll
                FROM users
                WHERE id = $1;
            "#,
            xid.as_bytes(),
        ).fetch_optional(*db).await.unwrap(),
        UserId::Discord(discord_id) => sqlx::query_as!(
            User,
            r#"
                SELECT
                    id, discord_id, banned, emeralds, vault_balance, vault_max, health, vote_streak, last_vote_at,
                    give_alert, shield_pearl_activated_at, last_daily_quest_reroll
                FROM users
                WHERE discord_id = $1;
            "#,
            discord_id,
        ).fetch_optional(*db).await.unwrap()
    };

    match user {
        Some(user) => Ok(Json(UserDetailsView::from(user))),
        None => Err(NotFoundError.into()),
    }
}

#[handler]
pub async fn register_new_user(
    db: Data<&sqlx::Pool<sqlx::Postgres>>,
    Path((user_id,)): Path<(UserId,)>,
    _: RequireAuthedClient,
) -> poem::Result<Json<UserDetailsView>> {
    match user_id {
        UserId::Xid(_) => Err(poem::Error::from_string(
            "You cannot register a new user using this type of ID",
            StatusCode::BAD_REQUEST,
        )),
        UserId::Discord(discord_id) => {
            let id = Xid::new();

            let user = sqlx::query_as!(
                User,
                r#"
                    INSERT INTO users
                        (id, discord_id)
                    VALUES ($1, $2)
                    ON CONFLICT (discord_id) DO NOTHING
                    RETURNING
                        id, discord_id, banned, emeralds, vault_balance, vault_max, health, vote_streak, last_vote_at,
                        give_alert, shield_pearl_activated_at, last_daily_quest_reroll
                    "#,
                id.as_bytes(), discord_id
            ).fetch_one(*db).await.unwrap();

            Ok(Json(UserDetailsView::from(user)))
        }
    }
}
