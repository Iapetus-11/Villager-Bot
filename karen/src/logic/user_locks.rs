use chrono::{DateTime, Utc};
use sqlx::PgConnection;

use crate::common::xid::Xid;

pub const ECONOMY_LOCK: &str = "economy";

#[derive(Debug)]
pub enum UserLockError {
    ConflictingLock,
    UserDoesNotExist,
    Sqlx(#[allow(unused)] sqlx::Error),
}

impl From<sqlx::Error> for UserLockError {
    fn from(value: sqlx::Error) -> Self {
        match value {
            sqlx::Error::Database(error) if error.is_unique_violation() => {
                UserLockError::ConflictingLock
            }
            sqlx::Error::Database(error) if error.is_foreign_key_violation() => {
                UserLockError::UserDoesNotExist
            }
            error => UserLockError::Sqlx(error),
        }
    }
}

pub async fn acquire_user_lock(
    db: &mut PgConnection,
    user_id: &Xid,
    lock_name: &str,
    until: DateTime<Utc>,
) -> Result<(), UserLockError> {
    let query_result = sqlx::query!(
        "INSERT INTO user_locks (user_id, lock_name, until) VALUES ($1, $2, $3)",
        user_id.as_bytes(),
        lock_name,
        until,
    )
    .execute(&mut *db)
    .await;

    let Err(query_error) = query_result else {
        return Ok(());
    };
    let query_error = UserLockError::from(query_error);

    match query_error {
        UserLockError::ConflictingLock => {
            let release_expired_locks_result = sqlx::query!(
                "DELETE FROM user_locks WHERE user_id = $1 AND NOW() >= until RETURNING lock_name",
                user_id.as_bytes(),
            )
            .fetch_optional(&mut *db)
            .await?;

            match release_expired_locks_result {
                Some(_) => Box::pin(acquire_user_lock(&mut *db, user_id, lock_name, until)).await,
                None => Err(UserLockError::ConflictingLock),
            }
        }
        err => Err(err),
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

/// Holds a user lock for the duration of the execution of the func. Returns `Err(UserLockError::ConflictingLock)` if
/// the lock is already held.
pub async fn use_user_lock<TReturn, TFunc: AsyncFnOnce(&mut PgConnection) -> TReturn>(
    db: &mut PgConnection,
    user_id: &Xid,
    lock_name: &str,
    until: DateTime<Utc>,
    func: TFunc,
) -> Result<TReturn, UserLockError> {
    acquire_user_lock(db, user_id, lock_name, until).await?;

    let result = func(db).await;

    release_user_lock(db, user_id, lock_name).await?;

    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;

    use chrono::{TimeDelta, Utc};

    use crate::common::testing::{CreateTestUser, PgPoolConn, create_test_user};

    #[sqlx::test]
    async fn test_acquire_user_lock(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        acquire_user_lock(
            &mut db,
            &user.id,
            ECONOMY_LOCK,
            Utc::now() + TimeDelta::seconds(10),
        )
        .await
        .unwrap();

        let acquire_2 = acquire_user_lock(
            &mut db,
            &user.id,
            ECONOMY_LOCK,
            Utc::now() + TimeDelta::seconds(20),
        )
        .await;
        assert!(matches!(acquire_2, Err(UserLockError::ConflictingLock)));

        let acquire_3 = acquire_user_lock(
            &mut db,
            &user.id,
            ECONOMY_LOCK,
            Utc::now() + TimeDelta::seconds(10),
        )
        .await;
        assert!(matches!(acquire_3, Err(UserLockError::ConflictingLock)));
    }

    #[sqlx::test]
    async fn test_acquire_user_lock_with_existing_expired_row(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        acquire_user_lock(
            &mut db,
            &user.id,
            ECONOMY_LOCK,
            Utc::now() - TimeDelta::seconds(10),
        )
        .await
        .unwrap();

        acquire_user_lock(
            &mut db,
            &user.id,
            ECONOMY_LOCK,
            Utc::now() + TimeDelta::seconds(20),
        )
        .await
        .unwrap();
    }

    #[sqlx::test]
    async fn test_two_different_locks_do_not_interfere(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        acquire_user_lock(
            &mut db,
            &user.id,
            "mine",
            Utc::now() + TimeDelta::seconds(10),
        )
        .await
        .unwrap();

        acquire_user_lock(
            &mut db,
            &user.id,
            "craft",
            Utc::now() + TimeDelta::seconds(10),
        )
        .await
        .unwrap();
    }

    #[sqlx::test]
    async fn test_release_lock(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        acquire_user_lock(
            &mut db,
            &user.id,
            ECONOMY_LOCK,
            Utc::now() + TimeDelta::seconds(10),
        )
        .await
        .unwrap();

        release_user_lock(&mut db, &user.id, ECONOMY_LOCK)
            .await
            .unwrap();

        let lock_count = sqlx::query!("SELECT COUNT(*) FROM user_locks")
            .fetch_one(&mut *db)
            .await
            .unwrap();
        assert_eq!(lock_count.count, Some(0));

        acquire_user_lock(
            &mut db,
            &user.id,
            ECONOMY_LOCK,
            Utc::now() + TimeDelta::seconds(10),
        )
        .await
        .unwrap();
    }

    #[sqlx::test]
    async fn test_release_nonexistent_lock(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        acquire_user_lock(
            &mut db,
            &user.id,
            ECONOMY_LOCK,
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

        let result = use_user_lock(&mut db, &user.id, "test", Utc::now(), async |_| 123)
            .await
            .unwrap();

        assert_eq!(result, 123);

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

        let result = use_user_lock(&mut db, &user.id, "test", Utc::now(), async |_| {
            panic!("This should never happen if the lock is already locked!");
        })
        .await;

        assert!(matches!(result, Err(UserLockError::ConflictingLock)));

        let lock_count = sqlx::query!("SELECT COUNT(*) FROM user_locks")
            .fetch_one(&mut *db)
            .await
            .unwrap();
        assert_eq!(lock_count.count, Some(1));
    }
}
