use chrono::TimeDelta;
use chrono::{DateTime, Utc};
use sqlx::PgConnection;
use sqlx::Connection;

use crate::common::xid::Xid;

struct CooldownRecord {
    until: DateTime<Utc>,
}

pub async fn get_cooldown(
    db: &mut PgConnection,
    user_id: &Xid,
    command: &str,
) -> Result<Option<DateTime<Utc>>, sqlx::Error> {
    Ok(sqlx::query_as!(
        CooldownRecord,
        "SELECT until FROM command_cooldowns WHERE user_id = $1 AND command = $2",
        user_id.as_bytes(),
        command,
    )
    .fetch_optional(&mut *db)
    .await?
    .map(|r| r.until))
}

pub async fn get_or_create_cooldown(db: &mut PgConnection, user_id: &Xid, command: &str, duration: TimeDelta) -> Result<(DateTime<Utc>, bool), sqlx::Error> {
    let mut cooldown = get_cooldown(&mut *db, user_id, command).await?;

    if let Some(cooldown) = cooldown {
        return Ok((cooldown, false));
    }

    let mut tx = db.begin().await?;

    todo!();
}
