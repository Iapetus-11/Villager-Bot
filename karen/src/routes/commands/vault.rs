use chrono::{TimeDelta, Utc};
use poem::{
    Body, IntoResponse, Response, handler,
    http::StatusCode,
    web::{Data, Json, Path},
};
use serde::{Deserialize, Serialize};

use std::error::Error as StdError;

use crate::{
    common::{security::RequireAuthedClient, xid::Xid},
    logic::{
        user_locks::{ECONOMY_LOCK, UserLockError, use_user_lock},
        users::{UpdateUser, get_or_create_user, update_user},
    },
};

#[derive(Deserialize)]
#[cfg_attr(test, derive(Serialize))]
struct VaultInteractionRequest {
    block_amount: i32,
}

#[derive(Debug, Serialize, thiserror::Error)]
#[cfg_attr(test, derive(Deserialize))]
pub enum VaultDepositError {
    #[error("User does not exist")]
    UserDoesNotExist,

    #[error("User lock {ECONOMY_LOCK:#?} cannot be acquired")]
    UserLockCannotBeAcquired,

    #[error("User does not have enough emeralds")]
    NotEnoughEmeralds,

    #[error("User does not have enough vault capacity")]
    NotEnoughVaultCapacity,
}

impl From<VaultDepositError> for poem::Error {
    fn from(val: VaultDepositError) -> Self {
        let status_code = match val {
            VaultDepositError::UserDoesNotExist => StatusCode::NOT_FOUND,
            VaultDepositError::UserLockCannotBeAcquired => StatusCode::CONFLICT,
            VaultDepositError::NotEnoughEmeralds => StatusCode::BAD_REQUEST,
            VaultDepositError::NotEnoughVaultCapacity => StatusCode::BAD_REQUEST,
        };

        poem::Error::from_response(
            Response::builder()
                .status(status_code)
                .body(Body::from_json(val).unwrap())
                .with_content_type("application/json")
                .into_response(),
        )
    }
}

#[handler]
pub async fn deposit(
    db: Data<&sqlx::PgPool>,
    data: Json<VaultInteractionRequest>,
    Path((user_id,)): Path<(Xid,)>,
    _: RequireAuthedClient,
) -> poem::Result<()> {
    let mut db = db.acquire().await.unwrap();

    #[derive(Debug)]
    enum InnerError {
        Other(#[allow(unused)] Box<dyn StdError + Send>),
        VaultDeposit(VaultDepositError),
    }

    let acquire_lock_result: Result<Result<(), InnerError>, _> = use_user_lock(
        &mut db,
        &user_id,
        ECONOMY_LOCK,
        Utc::now() + TimeDelta::seconds(5),
        async |db| {
            let user = get_or_create_user(db, &crate::common::user_id::UserId::Xid(user_id))
                .await
                .map_err(|e| InnerError::Other(Box::new(e)))?;

            let emeralds_sub = (data.block_amount * 9) as i64;

            if emeralds_sub > user.emeralds {
                return Err(InnerError::VaultDeposit(
                    VaultDepositError::NotEnoughEmeralds,
                ));
            }

            if data.block_amount + user.vault_balance > user.vault_max {
                return Err(InnerError::VaultDeposit(
                    VaultDepositError::NotEnoughVaultCapacity,
                ));
            }

            update_user(
                db,
                &user_id,
                &UpdateUser {
                    vault_balance: Some(user.vault_balance + data.block_amount),
                    emeralds: Some(user.emeralds - emeralds_sub),
                    ..UpdateUser::default()
                },
            )
            .await
            .map_err(|e| InnerError::Other(Box::new(e)))?;

            Ok(())
        },
    )
    .await;

    match acquire_lock_result {
        Err(UserLockError::UserDoesNotExist) => Err(VaultDepositError::UserDoesNotExist),
        Err(UserLockError::ConflictingLock) => Err(VaultDepositError::UserLockCannotBeAcquired),
        Ok(Err(InnerError::VaultDeposit(error))) => Err(error),
        res => {
            res.unwrap().unwrap(); // Panic (and 500) for errors which aren't transformed to a response error
            Ok(())
        }
    }
    .map_err(poem::Error::from)?;

    Ok(())
}

#[handler]
pub async fn withdraw(
    db: Data<&sqlx::PgPool>,
    data: Json<VaultInteractionRequest>,
    Path((user_id,)): Path<(Xid,)>,
    _: RequireAuthedClient,
) {
    todo!();
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::common::testing::{create_test_user, setup_api_test_client};
    use crate::{
        common::{testing::CreateTestUser, user_id::UserId},
        logic::users::get_user,
    };
    use sqlx::PgPool;

    mod test_deposit {
        use crate::logic::user_locks::acquire_user_lock;

        use super::*;

        #[sqlx::test]
        fn test_success(db_pool: PgPool) {
            let mut db = db_pool.acquire().await.unwrap();

            let client = setup_api_test_client(db_pool);

            let user = create_test_user(
                &mut db,
                CreateTestUser {
                    emeralds: 420,
                    vault_balance: 3,
                    vault_max: 66,
                    ..CreateTestUser::default()
                },
            )
            .await;

            let response = client
                .post(format!("/commands/vault/{}/deposit/", *user.id))
                .body_json(&VaultInteractionRequest { block_amount: 4 })
                .send()
                .await;

            response.assert_status_is_ok();
            response.assert_text("").await;

            let user = get_user(&mut db, &UserId::Xid(user.id))
                .await
                .unwrap()
                .unwrap();

            assert_eq!(user.emeralds, 420 - (4 * 9));
            assert_eq!(user.vault_balance, 3 + 4);
            assert_eq!(user.vault_max, 66);
        }

        #[sqlx::test]
        fn test_user_does_not_exist(db_pool: PgPool) {
            let fake_user_id = Xid::new();

            let client = setup_api_test_client(db_pool);

            let response = client
                .post(format!("/commands/vault/{}/deposit/", *fake_user_id))
                .body_json(&VaultInteractionRequest { block_amount: 100 })
                .send()
                .await;

            response.assert_status(StatusCode::NOT_FOUND);
            response
                .assert_json(VaultDepositError::UserDoesNotExist)
                .await;
        }

        #[sqlx::test]
        fn test_user_already_locked(db_pool: PgPool) {
            let mut db = db_pool.acquire().await.unwrap();

            let client = setup_api_test_client(db_pool);

            let user = create_test_user(
                &mut db,
                CreateTestUser {
                    emeralds: 420,
                    vault_balance: 3,
                    vault_max: 66,
                    ..CreateTestUser::default()
                },
            )
            .await;

            acquire_user_lock(
                &mut db,
                &user.id,
                ECONOMY_LOCK,
                Utc::now() + TimeDelta::seconds(5),
            )
            .await
            .unwrap();

            let response = client
                .post(format!("/commands/vault/{}/deposit/", *user.id))
                .body_json(&VaultInteractionRequest { block_amount: 4 })
                .send()
                .await;

            response.assert_status(StatusCode::CONFLICT);
            response
                .assert_json(VaultDepositError::UserLockCannotBeAcquired)
                .await;
        }

        #[sqlx::test]
        fn test_user_is_too_poor(db_pool: PgPool) {
            let mut db = db_pool.acquire().await.unwrap();

            let client = setup_api_test_client(db_pool);

            let user = create_test_user(
                &mut db,
                CreateTestUser {
                    emeralds: 18,
                    vault_balance: 3,
                    vault_max: 66,
                    ..CreateTestUser::default()
                },
            )
            .await;

            let response = client
                .post(format!("/commands/vault/{}/deposit/", *user.id))
                .body_json(&VaultInteractionRequest { block_amount: 3 })
                .send()
                .await;

            response.assert_status(StatusCode::BAD_REQUEST);
            response.assert_json(VaultDepositError::NotEnoughEmeralds).await;
        }

        #[sqlx::test]
        fn test_not_enough_vault_capacity(db_pool: PgPool) {
            let mut db = db_pool.acquire().await.unwrap();

            let client = setup_api_test_client(db_pool);

            let user = create_test_user(
                &mut db,
                CreateTestUser {
                    emeralds: 1000000,
                    vault_balance: 0,
                    vault_max: 2,
                    ..CreateTestUser::default()
                },
            )
            .await;

            let response = client
                .post(format!("/commands/vault/{}/deposit/", *user.id))
                .body_json(&VaultInteractionRequest { block_amount: 3 })
                .send()
                .await;

            response.assert_status(StatusCode::BAD_REQUEST);
            response.assert_json(VaultDepositError::NotEnoughVaultCapacity).await;
        }
    }
}
