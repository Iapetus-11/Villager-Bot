use std::error::Error as StdError;

use chrono::{DateTime, Utc};
use sqlx::PgConnection;

use crate::common::xid::Xid;

pub async fn acquire_user_lock(
    db: &mut PgConnection,
    user_id: &Xid,
    lock_name: &str,
    until: DateTime<Utc>,
) -> Result<bool, sqlx::Error> {
    let query_result = sqlx::query!(
        "INSERT INTO user_locks (user_id, lock_name, until) VALUES ($1, $2, $3)",
        user_id.as_bytes(),
        lock_name,
        until,
    )
    .execute(&mut *db)
    .await;

    match query_result {
        Ok(_) => Ok(true),
        Err(sqlx::Error::Database(error)) if error.is_unique_violation() => {
            let release_expired_locks_result = sqlx::query!(
                "DELETE FROM user_locks WHERE user_id = $1 AND NOW() >= until RETURNING lock_name",
                user_id.as_bytes(),
            )
            .fetch_optional(&mut *db)
            .await?;

            match release_expired_locks_result {
                Some(_) => Box::pin(acquire_user_lock(&mut *db, user_id, lock_name, until)).await,
                None => Ok(false),
            }
        }
        Err(error) => Err(error),
    }
}

pub async fn release_user_lock(
    db: &mut PgConnection,
    user_id: &Xid,
    lock_name: &str,
) -> Result<(), sqlx::Error> {
    sqlx::query!(
        "DELETE FROM user_locks WHERE user_id = $1 AND lock_name = $2",
        user_id.as_bytes(),
        lock_name.into()
    )
    .execute(&mut *db)
    .await?;

    Ok(())
}

/// Holds a user lock for the duration of the execution of the func. Returns Ok(None) if the lock is already held
pub async fn use_user_lock<TRet, TFunc: AsyncFn() -> Result<TRet, Box<dyn StdError>>>(
    db: &mut PgConnection,
    user_id: &Xid,
    lock_name: &str,
    until: DateTime<Utc>,
    func: TFunc,
) -> Result<Option<TRet>, Box<dyn StdError>> {
    let did_acquire = acquire_user_lock(db, user_id, lock_name, until).await?;

    if !did_acquire {
        return Ok(None);
    }

    let result = func().await;

    release_user_lock(db, user_id, lock_name).await?;

    Ok(Some(result?))
}

#[cfg(test)]
mod tests {
    use super::*;

    use chrono::{TimeDelta, Utc};

    use crate::common::testing::{CreateTestUser, PgPoolConn, create_test_user};

    #[sqlx::test]
    async fn test_acquire_user_lock(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        let acquire_1 = acquire_user_lock(
            &mut db,
            &user.id,
            "economy",
            Utc::now() + TimeDelta::seconds(10),
        )
        .await
        .unwrap();
        assert!(acquire_1);

        let acquire_2 = acquire_user_lock(
            &mut db,
            &user.id,
            "economy",
            Utc::now() + TimeDelta::seconds(20),
        )
        .await
        .unwrap();
        assert!(!acquire_2);

        let acquire_3 = acquire_user_lock(
            &mut db,
            &user.id,
            "economy",
            Utc::now() + TimeDelta::seconds(10),
        )
        .await
        .unwrap();
        assert!(!acquire_3);
    }

    #[sqlx::test]
    async fn test_acquire_user_lock_with_existing_expired_row(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        let acquire_1 = acquire_user_lock(
            &mut db,
            &user.id,
            "economy",
            Utc::now() - TimeDelta::seconds(10),
        )
        .await
        .unwrap();
        assert!(acquire_1);

        let acquire_2 = acquire_user_lock(
            &mut db,
            &user.id,
            "economy",
            Utc::now() + TimeDelta::seconds(20),
        )
        .await
        .unwrap();
        assert!(acquire_2);
    }

    #[sqlx::test]
    async fn test_two_different_locks_do_not_interfere(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        let acquire_1 = acquire_user_lock(
            &mut db,
            &user.id,
            "mine",
            Utc::now() + TimeDelta::seconds(10),
        )
        .await
        .unwrap();
        assert!(acquire_1);

        let acquire_2 = acquire_user_lock(
            &mut db,
            &user.id,
            "craft",
            Utc::now() + TimeDelta::seconds(10),
        )
        .await
        .unwrap();
        assert!(acquire_2);
    }

    #[sqlx::test]
    async fn test_release_lock(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        assert!(
            acquire_user_lock(
                &mut db,
                &user.id,
                "economy",
                Utc::now() + TimeDelta::seconds(10),
            )
            .await
            .unwrap()
        );

        release_user_lock(&mut db, &user.id, "economy")
            .await
            .unwrap();

        let lock_count = sqlx::query!("SELECT COUNT(*) FROM user_locks")
            .fetch_one(&mut *db)
            .await
            .unwrap();
        assert_eq!(lock_count.count, Some(0));

        assert!(
            acquire_user_lock(
                &mut db,
                &user.id,
                "economy",
                Utc::now() + TimeDelta::seconds(10),
            )
            .await
            .unwrap()
        );
    }

    #[sqlx::test]
    async fn test_release_nonexistent_lock(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        acquire_user_lock(
            &mut db,
            &user.id,
            "economy",
            Utc::now() + TimeDelta::seconds(10),
        )
        .await
        .unwrap();

        release_user_lock(&mut db, &user.id, "other_lock")
            .await
            .unwrap();

        let lock_count = sqlx::query!("SELECT COUNT(*) FROM user_locks")
            .fetch_one(&mut *db)
            .await
            .unwrap();
        assert_eq!(lock_count.count, Some(1));
    }

    #[sqlx::test]
    async fn test_use_user_lock(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        let result = use_user_lock(&mut db, &user.id, "test", Utc::now(), async || Ok(123))
            .await
            .unwrap();

        assert_eq!(result, Some(123));

        let lock_count = sqlx::query!("SELECT COUNT(*) FROM user_locks")
            .fetch_one(&mut *db)
            .await
            .unwrap();
        assert_eq!(lock_count.count, Some(0));
    }

    #[sqlx::test]
    async fn test_use_user_lock_when_already_locked(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        acquire_user_lock(
            &mut db,
            &user.id,
            "test",
            Utc::now() + TimeDelta::seconds(10),
        )
        .await
        .unwrap();

        let result: Option<()> = use_user_lock(&mut db, &user.id, "test", Utc::now(), async || {
            panic!();
        })
        .await
        .unwrap();

        assert_eq!(result, None);

        let lock_count = sqlx::query!("SELECT COUNT(*) FROM user_locks")
            .fetch_one(&mut *db)
            .await
            .unwrap();
        assert_eq!(lock_count.count, Some(1));
    }
}
