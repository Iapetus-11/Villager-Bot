use sqlx::{Arguments, PgConnection, postgres::PgArguments};

use crate::common::xid::Xid;

#[derive(Debug)]
pub enum LeaderboardBump {
    PillagedEmeralds(i64),
    MobsKilled(i64),
    FishFished(i64),
    Commands(i64),
    WeekCommands(i64),
    CropsPlanted(i64),
    TrashEmptied(i64),
    WeekEmeralds(i64),
    DailyQuests(i32),
    WeekDailyQuests(i16),
}

impl LeaderboardBump {
    fn column_name(&self) -> String {
        match self {
            LeaderboardBump::PillagedEmeralds(_) => "pillaged_emeralds",
            LeaderboardBump::MobsKilled(_) => "mobs_killed",
            LeaderboardBump::FishFished(_) => "fish_fished",
            LeaderboardBump::Commands(_) => "commands",
            LeaderboardBump::WeekCommands(_) => "week_commands",
            LeaderboardBump::CropsPlanted(_) => "crops_planted",
            LeaderboardBump::TrashEmptied(_) => "trash_emptied",
            LeaderboardBump::WeekEmeralds(_) => "week_emeralds",
            LeaderboardBump::DailyQuests(_) => "daily_quests",
            LeaderboardBump::WeekDailyQuests(_) => "week_daily_quests",
        }
        .to_string()
    }
}

pub async fn ensure_user_has_leaderboard(
    db: &mut PgConnection,
    user_id: &Xid,
) -> Result<(), sqlx::Error> {
    sqlx::query!(
        "INSERT INTO leaderboards (user_id, week) VALUES ($1, DATE_TRUNC('DAY', NOW())) ON CONFLICT DO NOTHING",
        user_id.as_bytes()
    )
    .execute(&mut *db)
    .await
    .map(|_| ())
}

pub async fn bump_user_leaderboard(
    db: &mut PgConnection,
    user_id: &Xid,
    bumps: &[LeaderboardBump],
) -> Result<(), sqlx::Error> {
    let set_columns_sql = bumps
        .iter()
        .enumerate()
        .map(|(idx, bump)| format!("{0}={0}+${1}", bump.column_name(), idx + 2))
        .collect::<Vec<_>>()
        .join(", ");
    let query_sql = format!("UPDATE leaderboards SET {set_columns_sql} WHERE user_id = $1");

    let mut query_args = PgArguments::default();
    query_args.add(user_id.as_bytes()).unwrap();
    for bump in bumps {
        match bump {
            LeaderboardBump::PillagedEmeralds(v) => query_args.add(v),
            LeaderboardBump::MobsKilled(v) => query_args.add(v),
            LeaderboardBump::FishFished(v) => query_args.add(v),
            LeaderboardBump::Commands(v) => query_args.add(v),
            LeaderboardBump::WeekCommands(v) => query_args.add(v),
            LeaderboardBump::CropsPlanted(v) => query_args.add(v),
            LeaderboardBump::TrashEmptied(v) => query_args.add(v),
            LeaderboardBump::WeekEmeralds(v) => query_args.add(v),
            LeaderboardBump::DailyQuests(v) => query_args.add(v),
            LeaderboardBump::WeekDailyQuests(v) => query_args.add(v),
        }
        .unwrap()
    }

    sqlx::query_with(&query_sql, query_args)
        .fetch_optional(&mut *db)
        .await
        .map(|_| ())
}

#[cfg(test)]
mod tests {
    use crate::common::testing::{CreateTestUser, PgPoolConn, create_test_user};

    use super::*;

    #[sqlx::test]
    async fn test_bump_user_leaderboard(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;
        ensure_user_has_leaderboard(&mut db, &user.id)
            .await
            .unwrap();

        bump_user_leaderboard(
            &mut db,
            &user.id,
            &[
                LeaderboardBump::PillagedEmeralds(1),
                LeaderboardBump::MobsKilled(2),
                LeaderboardBump::FishFished(3),
                LeaderboardBump::Commands(4),
                LeaderboardBump::WeekCommands(5),
                LeaderboardBump::CropsPlanted(6),
                LeaderboardBump::TrashEmptied(7),
                LeaderboardBump::WeekEmeralds(8),
                LeaderboardBump::DailyQuests(9),
                LeaderboardBump::WeekDailyQuests(10),
            ],
        )
        .await
        .unwrap();

        let leaderboard_row = sqlx::query!(r#"
                SELECT
                    pillaged_emeralds, mobs_killed, fish_fished, commands, week_commands, crops_planted, trash_emptied,
                    week_emeralds, daily_quests, week_daily_quests
                FROM leaderboards
            "#)
            .fetch_one(&mut *db)
            .await
            .unwrap();
        assert_eq!(leaderboard_row.pillaged_emeralds, 1);
        assert_eq!(leaderboard_row.mobs_killed, 2);
        assert_eq!(leaderboard_row.fish_fished, 3);
        assert_eq!(leaderboard_row.commands, 4);
        assert_eq!(leaderboard_row.week_commands, 5);
        assert_eq!(leaderboard_row.crops_planted, 6);
        assert_eq!(leaderboard_row.trash_emptied, 7);
        assert_eq!(leaderboard_row.week_emeralds, 8);
        assert_eq!(leaderboard_row.daily_quests, 9);
        assert_eq!(leaderboard_row.week_daily_quests, 10);
    }
}
