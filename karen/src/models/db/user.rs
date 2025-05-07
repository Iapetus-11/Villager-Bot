use chrono::{DateTime, Utc};
use serde::Serialize;
use sqlx::FromRow;

use crate::common::xid::Xid;

#[derive(Debug, FromRow, Serialize)]
pub struct User {
    pub id: Xid,
    pub discord_id: Option<i64>,
    pub banned: bool,
    pub emeralds: i64,
    pub vault_balance: i32,
    pub vault_max: i32,
    pub health: i16,
    pub vote_streak: i32,
    pub last_vote_at: Option<DateTime<Utc>>,
    pub give_alert: bool,
    pub shield_pearl_activated_at: Option<DateTime<Utc>>,
    pub last_daily_quest_reroll: Option<DateTime<Utc>>,
    pub modified_at: DateTime<Utc>,
}
