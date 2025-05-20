use chrono::{DateTime, Utc};
use sqlx::PgConnection;

use crate::common::xid::Xid;

pub async fn log_command_execution(
    db: &mut PgConnection,
    user_id: &Xid,
    command: &str,
    discord_guild_id: Option<i64>,
    at: DateTime<Utc>,
) -> Result<(), sqlx::Error> {
    sqlx::query!(
        "INSERT INTO command_executions (user_id, command, discord_guild_id, at) VALUES ($1, $2, $3, $4)",
        user_id.as_bytes(), command, discord_guild_id, at,
    ).execute(&mut *db).await?;

    // TODO: Update leaderboard, mob spawning

    Ok(())
}
