use chrono::{DateTime, Utc};
use sqlx::PgConnection;

use crate::common::xid::Xid;

pub async fn log_command_execution(
    db: &mut PgConnection,
    discord_guild_id: i64,
    command: &str,
    is_slash: bool,
    at: DateTime<Utc>,
    user_id: &Xid,
) -> Result<(), sqlx::Error> {
    sqlx::query!(
        "INSERT INTO command_executions (guild_id, command, is_slash, at, user_id) VALUES ($1, $2, $3, $4, $5)",
        discord_guild_id, command, is_slash, at, user_id.as_bytes(),
    ).execute(&mut *db).await?;

    // TODO: Update leaderboard, mob spawning

    Ok(())
}
