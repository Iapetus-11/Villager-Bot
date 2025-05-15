use chrono::{DateTime, TimeDelta, Utc};
use poem::{
    handler,
    http::StatusCode,
    web::{Data, Json},
};
use serde::{Deserialize, Serialize};

use crate::{
    common::{data::COMMANDS_DATA, security::RequireAuthedClient, xid::Xid},
    logic::cooldowns::get_or_create_cooldown,
};

#[derive(Deserialize)]
#[cfg_attr(test, derive(Serialize))]
struct CheckCooldownRequest {
    user_id: Xid,
    command: String,
    from: DateTime<Utc>,
}

#[derive(Debug, Serialize)]
#[cfg_attr(test, derive(Deserialize))]
struct CheckCooldownResponse {
    already_on_cooldown: bool,
    until: DateTime<Utc>,
}

#[handler]
pub async fn check_cooldown(
    db: Data<&sqlx::PgPool>,
    data: Json<CheckCooldownRequest>,
    _: RequireAuthedClient,
) -> Result<Json<CheckCooldownResponse>, poem::Error> {
    let Some(cooldown_seconds) = COMMANDS_DATA.cooldowns.get(&data.command) else {
        return Err(poem::Error::from_string(
            format!("Command {:#?} does not have a cooldown", data.command),
            StatusCode::BAD_REQUEST,
        ));
    };

    // This cooldown will be used if there is no existing cooldown
    let cooldown = data.from + TimeDelta::seconds(*cooldown_seconds as i64);

    let mut db = db.acquire().await.unwrap();

    let (until, already_on_cooldown) =
        get_or_create_cooldown(&mut db, &data.user_id, &data.command, cooldown)
            .await
            .unwrap();

    Ok(Json(CheckCooldownResponse {
        already_on_cooldown,
        until,
    }))
}

#[cfg(test)]
mod tests {
    use crate::common::testing::{CreateTestUser, create_test_user, setup_api_test_client};

    use super::*;
    use chrono::SubsecRound;
    use sqlx::PgPool;

    #[sqlx::test]
    async fn test_check_cooldown_nonexistent_cooldown(db_pool: PgPool) {
        let mut db = db_pool.acquire().await.unwrap();

        let command = "mine".to_string();
        let expected_cooldown_seconds = COMMANDS_DATA.cooldowns.get(&command).unwrap();
        let user = create_test_user(&mut db, CreateTestUser::default()).await;
        let from = Utc::now();

        let client = setup_api_test_client(db_pool);
        let response = client
            .post("/game/cooldowns/check/")
            .body_json(&CheckCooldownRequest {
                user_id: user.id,
                command,
                from,
            })
            .send()
            .await;

        response.assert_status_is_ok();
        response
            .assert_json(CheckCooldownResponse {
                already_on_cooldown: false,
                until: from + TimeDelta::seconds(*expected_cooldown_seconds as i64),
            })
            .await;
    }

    #[sqlx::test]
    async fn test_check_cooldown_existing_already(db_pool: PgPool) {
        let mut db = db_pool.acquire().await.unwrap();

        let command = "mine".to_string();
        let user = create_test_user(&mut db, CreateTestUser::default()).await;
        let from: DateTime<Utc> = Utc::now();
        let (existing_cooldown, _) = get_or_create_cooldown(
            &mut db,
            &user.id,
            &command,
            Utc::now().trunc_subsecs(6) + TimeDelta::seconds(69),
        )
        .await
        .unwrap();

        let client = setup_api_test_client(db_pool);
        let response = client
            .post("/game/cooldowns/check/")
            .body_json(&CheckCooldownRequest {
                user_id: user.id,
                command,
                from,
            })
            .send()
            .await;

        response.assert_status_is_ok();
        response
            .assert_json(CheckCooldownResponse {
                already_on_cooldown: true,
                until: existing_cooldown,
            })
            .await;
    }

    #[sqlx::test]
    async fn test_command_does_not_have_cooldown(db_pool: PgPool) {
        let mut db = db_pool.acquire().await.unwrap();

        let user = create_test_user(&mut db, CreateTestUser::default()).await;
        let command = "help";

        let client = setup_api_test_client(db_pool);
        let response = client
            .post("/game/cooldowns/check/")
            .body_json(&CheckCooldownRequest {
                user_id: user.id,
                command: command.to_string(),
                from: Utc::now(),
            })
            .send()
            .await;

        response.assert_status(StatusCode::BAD_REQUEST);
        response
            .assert_text(format!("Command {command:#?} does not have a cooldown"))
            .await;
    }
}
