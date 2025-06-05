use chrono::{DateTime, Utc};
use poem::{
    handler,
    web::{Data, Json, Path},
};
use serde::Serialize;

use crate::{
    common::user_id::UserId,
    logic::commands::profile::{ProfileCommandData, get_profile_command_data},
};

#[derive(Serialize)]
#[cfg_attr(test, derive(serde::Deserialize))]
struct ProfileCommandDataView {
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

impl From<ProfileCommandData> for ProfileCommandDataView {
    fn from(value: ProfileCommandData) -> Self {
        Self {
            net_wealth: value.net_wealth,
            mooderalds: value.mooderalds,
            vote_streak: value.vote_streak,
            can_vote: value.can_vote,
            next_vote_time: value.next_vote_time,
            pickaxe: value.pickaxe,
            sword: value.sword,
            hoe: value.hoe,
            active_effects: value.active_effects,
        }
    }
}

#[handler]
pub async fn get_data(
    db: Data<&sqlx::PgPool>,
    Path((user_id,)): Path<(UserId,)>,
) -> Result<Json<ProfileCommandDataView>, poem::Error> {
    let mut db = db.acquire().await.unwrap();

    Ok(Json(ProfileCommandDataView::from(
        get_profile_command_data(&mut db, &user_id).await.unwrap(),
    )))
}

#[cfg(test)]
mod tests {
    use crate::common::testing::CreateTestUser;
    use crate::common::testing::create_test_user;
    use crate::common::testing::setup_api_test_client;
    use sqlx::PgPool;

    mod test_get_data {
        use super::*;

        #[sqlx::test]
        async fn test_success(db_pool: PgPool) {
            let mut db = db_pool.acquire().await.unwrap();

            let user = create_test_user(
                &mut db,
                CreateTestUser {
                    emeralds: 69,
                    vault_balance: 11,
                    vault_max: 23,
                    ..CreateTestUser::default()
                },
            )
            .await;

            let client = setup_api_test_client(db_pool);

            let response = client
                .get(format!("/commands/profile/{}/", *user.id))
                .send()
                .await;

            response.assert_status_is_ok();
        }
    }
}
