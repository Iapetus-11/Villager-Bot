use std::error::Error as StdError;

use chrono::{DateTime, TimeDelta, Utc};
use serde::Serialize;
use sqlx::PgConnection;

use crate::{
    common::user_id::UserId,
    logic::{
        items::get_user_items,
        user_effects::get_active_user_effects,
        user_tools::get_user_tools,
        users::{get_or_create_user, get_user_net_wealth, partial_update_user},
    },
};

#[derive(Debug, Serialize)]
pub struct ProfileCommandData {
    net_wealth: i64,
    mooderalds: i64,
    vote_streak: i32,
    can_vote: bool,
    next_vote_time: Option<DateTime<Utc>>,
    pickaxe: String,
    sword: String,
    hoe: String,
    active_effects: Vec<String>,
}

pub async fn get_profile_command_data(
    db: &mut PgConnection,
    user_id: &UserId,
) -> Result<ProfileCommandData, Box<dyn StdError>> {
    let mut user = get_or_create_user(&mut *db, user_id).await?;
    
    let tools = get_user_tools(&mut *db, &user.id).await?;
    let net_wealth = get_user_net_wealth(&mut *db, &user.id).await?;
    let relevant_items = get_user_items(&mut *db, &user.id, Some(&["Mooderald".into()])).await?;
    let active_effects = get_active_user_effects(&mut *db, &user.id).await?;

    match user.last_vote_at {
        Some(last_vote_at) if last_vote_at < Utc::now() - TimeDelta::hours(36) => {
            user.vote_streak = 0;
            partial_update_user(&mut *db, &user.id, update_data)
        },
        _ => {},
    }

    let can_vote = match user.last_vote_at {
        None => true,
        Some(lv) => lv < (Utc::now() - TimeDelta::hours(12)),
    };
    let next_vote_time = user.last_vote_at.map(|lv| lv + TimeDelta::hours(12));

    let mooderald_count = relevant_items
        .iter()
        .find(|i| i.name == "Mooderald")
        .map(|i| i.amount)
        .unwrap_or(0);

    Ok(ProfileCommandData {
        net_wealth,
        mooderalds: mooderald_count,
        vote_streak: user.vote_streak,
        can_vote,
        next_vote_time,
        pickaxe: tools.pickaxe.to_string(),
        sword: tools.sword.to_string(),
        hoe: tools.hoe.to_string(),
        active_effects,
    })
}

#[cfg(test)]
mod tests {
    use chrono::SubsecRound;

    use super::*;

    use crate::common::testing::{CreateTestUser, PgPoolConn, create_test_user};

    #[sqlx::test]
    async fn test_can_vote_and_next_vote_time(mut db: PgPoolConn) {
        let now = Utc::now().trunc_subsecs(6);

        for (last_vote_at, expected_can_vote, expected_next_vote_time) in [
            (Some(now), false, Some(now + TimeDelta::hours(12))),
            (None, true, None),
            (
                Some(now - TimeDelta::hours(10)),
                false,
                Some(now + TimeDelta::hours(2)),
            ),
        ] {
            let user = create_test_user(
                &mut db,
                CreateTestUser {
                    last_vote_at,
                    discord_id: None,
                    ..CreateTestUser::default()
                },
            )
            .await;

            let profile_cmd_data = get_profile_command_data(&mut db, &UserId::Xid(user.id))
                .await
                .unwrap();

            assert_eq!(profile_cmd_data.can_vote, expected_can_vote);
            assert_eq!(profile_cmd_data.next_vote_time, expected_next_vote_time);
        }
    }
}
