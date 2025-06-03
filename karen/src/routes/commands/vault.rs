use chrono::{TimeDelta, Utc};
use poem::{
    Body, IntoResponse, Response, handler,
    http::StatusCode,
    web::{Data, Json, Path},
};
use serde::{Deserialize, Serialize};

use std::error::Error as StdError;

use crate::{
    common::{game_errors::GameError, security::RequireAuthedClient, xid::Xid},
    logic::{
        user_locks::{ECONOMY_LOCK, UserLockError, use_user_lock},
        users::{UpdateUser, get_or_create_user, update_user},
    },
};

#[derive(Deserialize)]
#[cfg_attr(test, derive(Serialize))]
#[serde(untagged)]
enum VaultInteractionBlocks {
    Amount(i32),
    Max,
}

#[derive(Deserialize)]
#[cfg_attr(test, derive(Serialize))]
struct VaultInteractionRequest {
    blocks: VaultInteractionBlocks,
}

#[derive(Debug, Serialize, thiserror::Error)]
#[cfg_attr(test, derive(Deserialize))]
pub enum VaultDepositError {
    #[error("User does not have enough vault capacity")]
    NotEnoughVaultCapacity,

    #[error("Cannot deposit a negative amount")]
    NonPositiveAmount,
}

impl From<VaultDepositError> for poem::Error {
    fn from(val: VaultDepositError) -> Self {
        let status_code = match val {
            VaultDepositError::NotEnoughVaultCapacity => StatusCode::BAD_REQUEST,
            VaultDepositError::NonPositiveAmount => StatusCode::BAD_REQUEST,
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
        Game(#[allow(unused)] GameError),
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

            let blocks = match data.blocks {
                VaultInteractionBlocks::Amount(blocks) => blocks,
                VaultInteractionBlocks::Max => (user.emeralds / 9) as i32,
            };

            if blocks <= 0 {
                return Err(InnerError::VaultDeposit(
                    VaultDepositError::NonPositiveAmount,
                ));
            }

            let emeralds_sub = blocks as i64 * 9;

            if emeralds_sub > user.emeralds {
                return Err(InnerError::Game(GameError::NotEnoughEmeralds));
            }

            if blocks + user.vault_balance > user.vault_max {
                return Err(InnerError::VaultDeposit(
                    VaultDepositError::NotEnoughVaultCapacity,
                ));
            }

            update_user(
                db,
                &user_id,
                &UpdateUser {
                    vault_balance: Some(user.vault_balance + blocks),
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
        Err(UserLockError::UserDoesNotExist) => Err(poem::Error::from(GameError::UserDoesNotExist)),
        Err(UserLockError::ConflictingLock) => {
            Err(poem::Error::from(GameError::UserLockCannotBeAcquired {
                lock: ECONOMY_LOCK.to_string(),
            }))
        }
        Ok(Err(InnerError::Game(error))) => Err(poem::Error::from(error)),
        Ok(Err(InnerError::VaultDeposit(error))) => Err(poem::Error::from(error)),
        res => {
            // Panic (and 500) for errors which aren't transformed to a response error
            res.unwrap().unwrap();
            Ok(())
        }
    }?;

    Ok(())
}

#[derive(Debug, Serialize, thiserror::Error)]
#[cfg_attr(test, derive(Deserialize))]
pub enum VaultWithdrawError {
    #[error("User does not have enough emerald blocks in their vault")]
    NotEnoughEmeraldBlocks,

    #[error("Cannot withdraw a negative amount")]
    NonPositiveAmount,
}

impl From<VaultWithdrawError> for poem::Error {
    fn from(val: VaultWithdrawError) -> Self {
        let status_code = match val {
            VaultWithdrawError::NotEnoughEmeraldBlocks => StatusCode::BAD_REQUEST,
            VaultWithdrawError::NonPositiveAmount => StatusCode::BAD_REQUEST,
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
pub async fn withdraw(
    db: Data<&sqlx::PgPool>,
    data: Json<VaultInteractionRequest>,
    Path((user_id,)): Path<(Xid,)>,
    _: RequireAuthedClient,
) -> poem::Result<()> {
    let mut db = db.acquire().await.unwrap();

    #[derive(Debug)]
    enum InnerError {
        Other(#[allow(unused)] Box<dyn StdError + Send>),
        VaultWithdraw(VaultWithdrawError),
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

            let blocks = match data.blocks {
                VaultInteractionBlocks::Amount(blocks) => blocks,
                VaultInteractionBlocks::Max => user.vault_balance,
            };

            if blocks <= 0 {
                return Err(InnerError::VaultWithdraw(
                    VaultWithdrawError::NonPositiveAmount,
                ));
            }

            let emeralds_add = (blocks * 9) as i64;

            if blocks > user.vault_balance {
                return Err(InnerError::VaultWithdraw(
                    VaultWithdrawError::NotEnoughEmeraldBlocks,
                ));
            }

            update_user(
                db,
                &user_id,
                &UpdateUser {
                    vault_balance: Some(user.vault_balance - blocks),
                    emeralds: Some(user.emeralds + emeralds_add),
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
        Err(UserLockError::UserDoesNotExist) => Err(poem::Error::from(GameError::UserDoesNotExist)),
        Err(UserLockError::ConflictingLock) => {
            Err(poem::Error::from(GameError::UserLockCannotBeAcquired {
                lock: ECONOMY_LOCK.to_string(),
            }))
        }
        Ok(Err(InnerError::VaultWithdraw(error))) => Err(poem::Error::from(error)),
        res => {
            // Panic (and 500) for errors which aren't transformed to a response error
            res.unwrap().unwrap();
            Ok(())
        }
    }?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::common::testing::{create_test_user, setup_api_test_client};
    use crate::logic::user_locks::acquire_user_lock;
    use crate::{
        common::{testing::CreateTestUser, user_id::UserId},
        logic::users::get_user,
    };
    use sqlx::PgPool;

    mod test_deposit {
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
                .body_json(&VaultInteractionRequest {
                    blocks: VaultInteractionBlocks::Amount(4),
                })
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
        async fn test_max(db_pool: PgPool) {
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
                .body_json(&VaultInteractionRequest {
                    blocks: VaultInteractionBlocks::Max,
                })
                .send()
                .await;

            response.assert_status_is_ok();
            response.assert_text("").await;

            let user = get_user(&mut db, &UserId::Xid(user.id))
                .await
                .unwrap()
                .unwrap();

            assert_eq!(user.emeralds, 420 - (46 * 9));
            assert_eq!(user.vault_balance, 3 + 46);
            assert_eq!(user.vault_max, 66);
        }

        #[sqlx::test]
        fn test_user_does_not_exist(db_pool: PgPool) {
            let fake_user_id = Xid::new();

            let client = setup_api_test_client(db_pool);

            let response = client
                .post(format!("/commands/vault/{}/deposit/", *fake_user_id))
                .body_json(&VaultInteractionRequest {
                    blocks: VaultInteractionBlocks::Amount(100),
                })
                .send()
                .await;

            response.assert_status(StatusCode::NOT_FOUND);
            response.assert_json(GameError::UserDoesNotExist).await;
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
                .body_json(&VaultInteractionRequest {
                    blocks: VaultInteractionBlocks::Amount(4),
                })
                .send()
                .await;

            response.assert_status(StatusCode::CONFLICT);
            response
                .assert_json(GameError::UserLockCannotBeAcquired {
                    lock: ECONOMY_LOCK.to_string(),
                })
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
                .body_json(&VaultInteractionRequest {
                    blocks: VaultInteractionBlocks::Amount(3),
                })
                .send()
                .await;

            response.assert_status(StatusCode::BAD_REQUEST);
            response.assert_json(GameError::NotEnoughEmeralds).await;
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
                .body_json(&VaultInteractionRequest {
                    blocks: VaultInteractionBlocks::Amount(3),
                })
                .send()
                .await;

            response.assert_status(StatusCode::BAD_REQUEST);
            response
                .assert_json(VaultDepositError::NotEnoughVaultCapacity)
                .await;
        }

        #[sqlx::test]
        fn test_non_positive_amount(db_pool: PgPool) {
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
                .body_json(&VaultInteractionRequest {
                    blocks: VaultInteractionBlocks::Amount(0),
                })
                .send()
                .await;

            response.assert_status(StatusCode::BAD_REQUEST);
            response
                .assert_json(VaultDepositError::NonPositiveAmount)
                .await;
        }
    }

    mod test_withdraw {
        use super::*;

        #[sqlx::test]
        fn test_success(db_pool: PgPool) {
            let mut db = db_pool.acquire().await.unwrap();

            let client = setup_api_test_client(db_pool);

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

            let response = client
                .post(format!("/commands/vault/{}/withdraw/", *user.id))
                .body_json(&VaultInteractionRequest {
                    blocks: VaultInteractionBlocks::Amount(4),
                })
                .send()
                .await;

            response.assert_status_is_ok();
            response.assert_text("").await;

            let user = get_user(&mut db, &UserId::Xid(user.id))
                .await
                .unwrap()
                .unwrap();

            assert_eq!(user.emeralds, 69 + (4 * 9));
            assert_eq!(user.vault_balance, 11 - 4);
            assert_eq!(user.vault_max, 23);
        }

        #[sqlx::test]
        fn test_max(db_pool: PgPool) {
            let mut db = db_pool.acquire().await.unwrap();

            let client = setup_api_test_client(db_pool);

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

            let response = client
                .post(format!("/commands/vault/{}/withdraw/", *user.id))
                .body_json(&VaultInteractionRequest {
                    blocks: VaultInteractionBlocks::Max,
                })
                .send()
                .await;

            response.assert_status_is_ok();
            response.assert_text("").await;

            let user = get_user(&mut db, &UserId::Xid(user.id))
                .await
                .unwrap()
                .unwrap();

            assert_eq!(user.emeralds, 69 + (11 * 9));
            assert_eq!(user.vault_balance, 0);
            assert_eq!(user.vault_max, 23);
        }

        #[sqlx::test]
        fn test_user_does_not_exist(db_pool: PgPool) {
            let fake_user_id = Xid::new();

            let client = setup_api_test_client(db_pool);

            let response = client
                .post(format!("/commands/vault/{}/withdraw/", *fake_user_id))
                .body_json(&VaultInteractionRequest {
                    blocks: VaultInteractionBlocks::Amount(420),
                })
                .send()
                .await;

            response.assert_status(StatusCode::NOT_FOUND);
            response.assert_json(GameError::UserDoesNotExist).await;
        }

        #[sqlx::test]
        fn test_user_already_locked(db_pool: PgPool) {
            let mut db = db_pool.acquire().await.unwrap();

            let client = setup_api_test_client(db_pool);

            let user = create_test_user(
                &mut db,
                CreateTestUser {
                    emeralds: 123456789,
                    vault_balance: 444,
                    vault_max: 444,
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
                .post(format!("/commands/vault/{}/withdraw/", *user.id))
                .body_json(&VaultInteractionRequest {
                    blocks: VaultInteractionBlocks::Amount(1),
                })
                .send()
                .await;

            response.assert_status(StatusCode::CONFLICT);
            response
                .assert_json(GameError::UserLockCannotBeAcquired {
                    lock: ECONOMY_LOCK.to_string(),
                })
                .await;
        }

        #[sqlx::test]
        fn test_not_enough_emerald_blocks(db_pool: PgPool) {
            let mut db = db_pool.acquire().await.unwrap();

            let client = setup_api_test_client(db_pool);

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

            let response = client
                .post(format!("/commands/vault/{}/withdraw/", *user.id))
                .body_json(&VaultInteractionRequest {
                    blocks: VaultInteractionBlocks::Amount(12),
                })
                .send()
                .await;

            response.assert_status(StatusCode::BAD_REQUEST);
            response
                .assert_json(VaultWithdrawError::NotEnoughEmeraldBlocks)
                .await;
        }

        #[sqlx::test]
        fn test_non_positive_amount(db_pool: PgPool) {
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
                .post(format!("/commands/vault/{}/withdraw/", *user.id))
                .body_json(&VaultInteractionRequest {
                    blocks: VaultInteractionBlocks::Amount(0),
                })
                .send()
                .await;

            response.assert_status(StatusCode::BAD_REQUEST);
            response
                .assert_json(VaultDepositError::NonPositiveAmount)
                .await;
        }
    }
}
