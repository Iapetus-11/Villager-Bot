use chrono::{DateTime, TimeDelta, Utc};
use poem::{
    Body, IntoResponse, Response,
    web::{Data, Json},
};
use serde::{Deserialize, Serialize};

use crate::{
    common::{data::COMMANDS_DATA, security::RequireAuthedClient, xid::Xid},
    logic::{command_cooldowns::get_or_create_cooldown, command_executions::log_command_execution},
};

#[derive(Debug, Deserialize)]
#[cfg_attr(test, derive(Serialize))]
struct CommandExecutionPreflightRequest {
    user_id: Xid,
    command: String,
    discord_guild_id: Option<i64>,
    at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
#[cfg_attr(test, derive(Serialize))]
struct CommandExecutionPreflightResponse {
    spawn_mob: bool,
}

#[derive(Debug, Serialize)]
#[cfg_attr(test, derive(Deserialize))]
#[serde(tag = "error_type", content = "error")]
enum PreflightErrorResponse {
    CommandOnCooldown { until: DateTime<Utc> },
}

#[poem::handler]
pub async fn preflight(
    db: Data<&sqlx::PgPool>,
    data: Json<CommandExecutionPreflightRequest>,
    _: RequireAuthedClient,
) -> Result<(), poem::Error> {
    let mut db = db.acquire().await.unwrap();

    if let Some(cooldown_seconds) = COMMANDS_DATA.cooldowns.get(&data.command) {
        // This cooldown will be used if there is no existing cooldown
        let cooldown = data.at + TimeDelta::seconds(*cooldown_seconds as i64);

        let (until, already_on_cooldown) =
            get_or_create_cooldown(&mut db, &data.user_id, &data.command, cooldown)
                .await
                .unwrap();

        if already_on_cooldown {
            return Err(poem::Error::from_response(
                Response::builder()
                    .body(
                        Body::from_json(PreflightErrorResponse::CommandOnCooldown { until })
                            .unwrap(),
                    )
                    .with_content_type("application/json")
                    .into_response(),
            ));
        }
    }

    // TODO: Update command executions leaderboard if the command is a qualifying economy command

    log_command_execution(
        &mut db,
        &data.user_id,
        &data.command,
        data.discord_guild_id,
        data.at,
    )
    .await
    .unwrap();

    Ok(())
}

#[cfg(test)]
mod tests {
    use chrono::SubsecRound;
    use sqlx::PgPool;

    use crate::common::testing::{create_test_user, setup_api_test_client, CreateTestUser, PgPoolConn};

    use super::*;

    #[sqlx::test]
    async fn test_success(db_pool: PgPool) {
        let mut db = db_pool.acquire().await.unwrap();

        let command = "mine".to_string();
        let user = create_test_user(&mut db, CreateTestUser::default()).await;
        let now: DateTime<Utc> = Utc::now();

        let client = setup_api_test_client(db_pool);
        let response = client
            .post("/game/command_executions/preflight/")
            .body_json(&CommandExecutionPreflightRequest {
                user_id: user.id,
                command,
                discord_guild_id: None,
                at: now,
            })
            .send()
            .await;

        response.assert_status_is_ok();
        response.assert_bytes(b"").await;
    }

    #[sqlx::test]
    async fn test_command_on_cooldown_already(db_pool: PgPool) {
        let mut db = db_pool.acquire().await.unwrap();

        let command = "mine".to_string();
        let user = create_test_user(&mut db, CreateTestUser::default()).await;
        let now: DateTime<Utc> = Utc::now();

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
            .post("/game/command_executions/preflight/")
            .body_json(&CommandExecutionPreflightRequest {
                user_id: user.id,
                command,
                discord_guild_id: None,
                at: now,
            })
            .send()
            .await;

        response.assert_status_is_ok();
        response
            .assert_json(PreflightErrorResponse::CommandOnCooldown { until: existing_cooldown })
            .await;
    }
}
