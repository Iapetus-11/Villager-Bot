use chrono::{DateTime, Utc};

#[derive(Debug)]
pub struct UserLeaderboard {
    pillaged_emeralds: i64,
    mobs_killed: i64,
    fish_fished: i64,
    commands: i64,
    crops_planted: i64,
    trash_emptied: i64,
    week_emeralds: i64,
    week_commands: i64,
    daily_quests: i32,
    week_daily_quests: i16,
    week: DateTime<Utc>,
}
