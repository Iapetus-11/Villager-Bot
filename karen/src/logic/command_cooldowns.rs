use chrono::{DateTime, Utc};
use sqlx::PgConnection;

use crate::common::xid::Xid;

pub async fn get_cooldown(
    db: &mut PgConnection,
    user_id: &Xid,
    command: &str,
) -> Result<Option<DateTime<Utc>>, sqlx::Error> {
    struct CooldownRecord {
        until: DateTime<Utc>,
    }

    Ok(sqlx::query_as!(
        CooldownRecord,
        "SELECT until FROM command_cooldowns WHERE user_id = $1 AND command = $2",
        user_id.as_bytes(),
        command,
    )
    .fetch_optional(&mut *db)
    .await?
    .map(|r| r.until))
}

/// Gets or creates a cooldown, returning a tuple containing the cooldown and true if there already was one
pub async fn get_or_create_cooldown(
    db: &mut PgConnection,
    user_id: &Xid,
    command: &str,
    default_cooldown: DateTime<Utc>,
) -> Result<(DateTime<Utc>, bool), sqlx::Error> {
    if let Some(cooldown) = get_cooldown(&mut *db, user_id, command).await? {
        return Ok((cooldown, true));
    }

    let creation_result = sqlx::query!(
        "INSERT INTO command_cooldowns (user_id, command, until) VALUES ($1, $2, $3)",
        user_id.as_bytes(),
        command,
        default_cooldown,
    )
    .execute(&mut *db)
    .await;

    match creation_result {
        Err(sqlx::Error::Database(error)) if error.is_unique_violation() => {
            return Ok((
                get_cooldown(&mut *db, user_id, command).await?.unwrap(),
                true,
            ));
        }
        Ok(_) => Ok((default_cooldown, false)),
        Err(error) => Err(error),
    }
}

#[cfg(test)]
mod tests {
    use chrono::{SubsecRound, TimeDelta};

    use crate::common::testing::{CreateTestUser, PgPoolConn, create_test_user};

    use super::*;

    async fn create_test_cooldown(
        db: &mut PgConnection,
        user_id: Xid,
        command: impl Into<String>,
        until: DateTime<Utc>,
    ) {
        sqlx::query!(
            r#"INSERT INTO command_cooldowns (user_id, command, until) VALUES ($1, $2, $3)"#,
            user_id.as_bytes(),
            command.into(),
            until,
        )
        .execute(&mut *db)
        .await
        .unwrap();
    }

    #[sqlx::test]
    async fn test_get_cooldown(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;
        let until = Utc::now().trunc_subsecs(6) + TimeDelta::seconds(5);

        create_test_cooldown(&mut db, user.id, "mine", until).await;
        create_test_cooldown(&mut db, user.id, "fish", Utc::now() + TimeDelta::minutes(1)).await;

        let cooldown = get_cooldown(&mut db, &user.id, "mine")
            .await
            .unwrap()
            .unwrap();

        assert_eq!(cooldown, until);
    }

    #[sqlx::test]
    async fn test_get_nonexistent_cooldown(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        create_test_cooldown(&mut db, user.id, "fish", Utc::now() + TimeDelta::minutes(1)).await;

        let cooldown = get_cooldown(&mut db, &user.id, "mine").await.unwrap();

        assert!(cooldown.is_none());
    }

    #[sqlx::test]
    async fn test_get_or_create_existing_cooldown(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;
        let until = Utc::now().trunc_subsecs(6) + TimeDelta::seconds(5);

        create_test_cooldown(&mut db, user.id, "mine", until).await;
        create_test_cooldown(&mut db, user.id, "fish", Utc::now() + TimeDelta::minutes(1)).await;

        let (cooldown, already_on_cooldown) = get_or_create_cooldown(
            &mut db,
            &user.id,
            "mine",
            Utc::now() + TimeDelta::seconds(100),
        )
        .await
        .unwrap();

        assert_eq!(cooldown, until);
        assert!(already_on_cooldown);
    }

    #[sqlx::test]
    async fn test_get_or_create_nonexistent_cooldown(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;
        let until = Utc::now() + TimeDelta::seconds(5);

        create_test_cooldown(&mut db, user.id, "fish", Utc::now() + TimeDelta::minutes(1)).await;

        let (cooldown, already_on_cooldown) =
            get_or_create_cooldown(&mut db, &user.id, "mine", until)
                .await
                .unwrap();

        assert_eq!(cooldown, until);
        assert!(!already_on_cooldown);
    }
}
