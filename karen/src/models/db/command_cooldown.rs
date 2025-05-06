use chrono::{DateTime, Utc};
use serde::Serialize;
use sqlx::prelude::FromRow;

use crate::common::xid::Xid;

#[derive(Debug, FromRow, Serialize)]
pub struct CommandCooldown {
    user_id: Xid,
    command: String,
    until: DateTime<Utc>,
}
