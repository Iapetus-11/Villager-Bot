use sqlx::Connection;
use sqlx::PgConnection;

use crate::{
    common::{user_id::UserId, xid::Xid},
    models::db::{Item, User},
};

use super::items::create_items;

pub async fn get_user(db: &mut PgConnection, id: &UserId) -> Result<Option<User>, sqlx::Error> {
    match id {
        UserId::Xid(xid) => sqlx::query_as!(
            User,
            r#"
                SELECT
                    id, discord_id, banned, emeralds, vault_balance, vault_max, health, vote_streak, last_vote_at,
                    give_alert, shield_pearl_activated_at, last_daily_quest_reroll, modified_at
                FROM users
                WHERE id = $1;
            "#,
            xid.as_bytes(),
        ).fetch_optional(&mut *db).await,
        UserId::Discord(discord_id) => sqlx::query_as!(
            User,
            r#"
                SELECT
                    id, discord_id, banned, emeralds, vault_balance, vault_max, health, vote_streak, last_vote_at,
                    give_alert, shield_pearl_activated_at, last_daily_quest_reroll, modified_at
                FROM users
                WHERE discord_id = $1;
            "#,
            discord_id,
        ).fetch_optional(&mut *db).await
    }
}

pub async fn create_default_user_items(
    db: &mut PgConnection,
    user_id: Xid,
) -> Result<(), sqlx::Error> {
    create_items(
        db,
        &[
            Item::new(user_id, "Wood Pickaxe", 0, 1, true, false),
            Item::new(user_id, "Wood Sword", 0, 1, true, false),
            Item::new(user_id, "Wood Hoe", 0, 1, true, false),
            Item::new(user_id, "Wheat Seed", 24, 5, false, true),
        ],
    )
    .await
}

#[derive(Debug, thiserror::Error)]
pub enum GetOrCreateUserError {
    #[error("Database error occurred {0:?}")]
    Database(sqlx::Error),

    #[error("User for Xid does not exist and a User cannot be created from an Xid")]
    CannotCreateUsingXid,
}

pub async fn get_or_create_user(
    db: &mut PgConnection,
    id: &UserId,
) -> Result<User, GetOrCreateUserError> {
    let mut user = get_user(&mut *db, id)
        .await
        .map_err(GetOrCreateUserError::Database)?;

    if user.is_none() {
        let creation_result = match id {
            UserId::Xid(_) => Err(GetOrCreateUserError::CannotCreateUsingXid),
            UserId::Discord(discord_id) => {
                let id = Xid::new();

                let mut tx = db.begin().await.map_err(GetOrCreateUserError::Database)?;

                create_default_user_items(&mut tx, id)
                    .await
                    .map_err(GetOrCreateUserError::Database)?;

                let user = sqlx::query_as!(
                    User,
                    r#"
                        INSERT INTO users
                            (id, discord_id)
                        VALUES ($1, $2)
                        ON CONFLICT (discord_id) DO NOTHING
                        RETURNING
                            id, discord_id, banned, emeralds, vault_balance, vault_max, health, vote_streak, last_vote_at,
                            give_alert, shield_pearl_activated_at, last_daily_quest_reroll, modified_at
                        "#,
                    id.as_bytes(), discord_id
                ).fetch_one(&mut *tx).await.map_err(GetOrCreateUserError::Database);

                tx.commit().await.map_err(GetOrCreateUserError::Database)?;

                user
            }
        };

        user = Some(match creation_result {
            Ok(discord_guild) => Ok(discord_guild),
            Err(GetOrCreateUserError::Database(sqlx::Error::Database(error)))
                if error.is_unique_violation() =>
            {
                get_user(&mut *db, id)
                    .await
                    .map(|u| u.unwrap())
                    .map_err(GetOrCreateUserError::Database)
            }
            error => error,
        }?);
    }

    Ok(user.unwrap())
}

#[cfg(test)]
mod tests {
    use chrono::{TimeDelta, Utc};

    use super::*;

    type PgPoolConn = sqlx::pool::PoolConnection<sqlx::Postgres>;

    async fn setup_user(db: &mut PgConnection) -> User {
        let user_id = Xid::new();

        let now = Utc::now();
        let ten_seconds_ago = now - TimeDelta::seconds(10);
        let two_hours_ago = now - TimeDelta::hours(2);
        let five_days_ago = now - TimeDelta::days(5);

        let user = User {
            id: user_id,
            discord_id: Some(536986067140608041),
            banned: true,
            emeralds: 420,
            vault_balance: 69,
            vault_max: 666,
            health: 19,
            vote_streak: 2,
            last_vote_at: Some(ten_seconds_ago),
            give_alert: false,
            shield_pearl_activated_at: Some(two_hours_ago),
            last_daily_quest_reroll: Some(five_days_ago),
            modified_at: now,
        };

        sqlx::query!(
            r#"
                INSERT INTO users (
                    id, discord_id, banned, emeralds, vault_balance, vault_max, health, vote_streak, last_vote_at,
                    give_alert, shield_pearl_activated_at, last_daily_quest_reroll, modified_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            "#,
            user.id.as_bytes(),
            user.discord_id,
            user.banned,
            user.emeralds,
            user.vault_balance,
            user.vault_max,
            user.health,
            user.vote_streak,
            user.last_vote_at,
            user.give_alert,
            user.shield_pearl_activated_at,
            user.last_daily_quest_reroll,
            user.modified_at,
        ).execute(&mut *db).await.unwrap();

        user
    }

    fn assert_users_eq(a: User, b: User) {
        assert_eq!(a.id, b.id);
        assert_eq!(a.discord_id, b.discord_id);
        assert_eq!(a.banned, b.banned);
        assert_eq!(a.emeralds, b.emeralds);
        assert_eq!(a.vault_balance, b.vault_balance);
        assert_eq!(a.vault_max, b.vault_max);
        assert_eq!(a.health, b.health);
        assert_eq!(a.vote_streak, b.vote_streak);
        assert_eq!(a.last_vote_at, b.last_vote_at);
        assert_eq!(a.give_alert, b.give_alert);
        assert_eq!(
            a.shield_pearl_activated_at,
            b.shield_pearl_activated_at
        );
        assert_eq!(
            a.last_daily_quest_reroll,
            b.last_daily_quest_reroll
        );
        assert_eq!(a.modified_at, b.modified_at);
    }

    #[sqlx::test]
    async fn test_get_user(mut db: PgPoolConn) {
        let expected_user = setup_user(&mut db).await;
        let user = get_user(&mut db, &UserId::Xid(expected_user.id))
            .await
            .unwrap()
            .unwrap();

        assert_users_eq(user, expected_user);
    }

    #[sqlx::test]
    async fn test_get_user_by_discord_id(mut db: PgPoolConn) {
        let expected_user = setup_user(&mut db).await;

        let user = get_user(
            &mut db,
            &UserId::Discord(expected_user.discord_id.unwrap()),
        )
        .await
        .unwrap()
        .unwrap();

        assert_users_eq(user, expected_user);
    }

    #[sqlx::test]
    async fn test_get_nonexistent_user(mut db: PgPoolConn) {
        let user = get_user(&mut db, &UserId::Xid(Xid::new())).await.unwrap();

        assert!(user.is_none());
    }

    #[sqlx::test]
    async fn test_get_or_create_nonexistent_user_from_discord(mut db: PgPoolConn) {
        let discord_id = 536986067140608041;
        let user_id = UserId::Discord(discord_id);

        let user = get_or_create_user(&mut db, &user_id).await.unwrap();

        assert_eq!(user.discord_id, Some(discord_id));

        // Check defaults
        assert!(!user.banned);
        assert_eq!(user.emeralds, 0);
        assert_eq!(user.vault_balance, 0);
        assert_eq!(user.vault_max, 1);
        assert_eq!(user.health, 20);
        assert_eq!(user.vote_streak, 0);
        assert_eq!(user.last_vote_at, None);
        assert!(user.give_alert);
        assert_eq!(user.shield_pearl_activated_at, None);
        assert_eq!(user.last_daily_quest_reroll, None);
        assert!(user.modified_at > (Utc::now() - TimeDelta::seconds(10)));
    }

    #[sqlx::test]
    async fn test_get_or_create_existing_user(mut db: PgPoolConn) {
        let expected_user = setup_user(&mut db).await;
        let user = get_or_create_user(&mut db, &UserId::Xid(expected_user.id))
            .await
            .unwrap();

        assert_users_eq(user, expected_user);
    }

    #[sqlx::test]
    async fn test_get_or_create_existing_user_from_discord(mut db: PgPoolConn) {
        let expected_user = setup_user(&mut db).await;
        let user = get_or_create_user(&mut db, &UserId::Discord(expected_user.discord_id.unwrap()))
            .await
            .unwrap();

        assert_users_eq(user, expected_user);
    }

    #[sqlx::test]
    async fn test_create_default_user_items(mut db: PgPoolConn) {
        todo!();
    }
}
