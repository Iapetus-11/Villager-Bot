use chrono::{DateTime, Utc};
use sqlx::PgConnection;

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

pub async fn get_or_create_cooldown(
    db: &mut PgConnection,
    user_id: &Xid,
    command: &str,
    default_cooldown: DateTime<Utc>,
) -> Result<(DateTime<Utc>, bool), sqlx::Error> {
    if let Some(cooldown) = get_cooldown(&mut *db, user_id, command).await? {
        return Ok((cooldown, false));
    }

    let creation_result = sqlx::query!(
        "INSERT INTO command_cooldowns (user_id, command, until) VALUES ($1, $2, $3)",
        user_id.as_bytes(),
        command,
        default_cooldown
    )
    .execute(&mut *db)
    .await;

    match creation_result {
        Err(sqlx::Error::Database(error)) if error.is_unique_violation() => {
            return Ok((
                get_cooldown(&mut *db, user_id, command).await?.unwrap(),
                true,
            ));
        }
        Ok(_) => Ok((default_cooldown, true)),
        Err(error) => Err(error),
    }
}
