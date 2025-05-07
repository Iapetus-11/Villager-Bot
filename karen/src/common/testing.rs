use chrono::{TimeDelta, Utc};
use sqlx::PgConnection;

use crate::models::db::User;

use super::xid::Xid;

pub type PgPoolConn = sqlx::pool::PoolConnection<sqlx::Postgres>;

pub async fn create_test_user(db: &mut PgConnection) -> User {
    let user_id = Xid::new();

    let now = Utc::now();
    let ten_seconds_ago = now - TimeDelta::seconds(10);
    let two_hours_ago = now - TimeDelta::hours(2);
    let five_days_ago = now - TimeDelta::days(5);

    let user = User {
        id: user_id,
        discord_id: Some(536986067140608041),
        banned: true,
        emeralds: 420,
        vault_balance: 69,
        vault_max: 666,
        health: 19,
        vote_streak: 2,
        last_vote_at: Some(ten_seconds_ago),
        give_alert: false,
        shield_pearl_activated_at: Some(two_hours_ago),
        last_daily_quest_reroll: Some(five_days_ago),
        modified_at: now,
    };

    sqlx::query!(
        r#"
            INSERT INTO users (
                id, discord_id, banned, emeralds, vault_balance, vault_max, health, vote_streak, last_vote_at,
                give_alert, shield_pearl_activated_at, last_daily_quest_reroll, modified_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        "#,
        user.id.as_bytes(),
        user.discord_id,
        user.banned,
        user.emeralds,
        user.vault_balance,
        user.vault_max,
        user.health,
        user.vote_streak,
        user.last_vote_at,
        user.give_alert,
        user.shield_pearl_activated_at,
        user.last_daily_quest_reroll,
        user.modified_at,
    ).execute(&mut *db).await.unwrap();

    user
}
