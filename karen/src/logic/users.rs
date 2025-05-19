use chrono::DateTime;
use chrono::Utc;
use serde::Deserialize;
use serde::Serialize;
use sqlx::Connection;
use sqlx::PgConnection;

use crate::{
    common::{user_id::UserId, xid::Xid},
    models::db::User,
};

use super::items::create_default_user_items;

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

                create_default_user_items(&mut tx, &id)
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

#[derive(Serialize, Deserialize, Default)]
pub struct UserUpdateData {
    #[serde(
        default,
        deserialize_with = "crate::common::serde_helpers::deserialize_maybe_undefined",
        skip_serializing_if = "Option::is_none"
    )]
    pub discord_id: Option<Option<i64>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub banned: Option<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub emeralds: Option<i64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub vault_balance: Option<i32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub vault_max: Option<i32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub health: Option<i16>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub vote_streak: Option<i32>,
    #[serde(
        default,
        deserialize_with = "crate::common::serde_helpers::deserialize_maybe_undefined",
        skip_serializing_if = "Option::is_none"
    )]
    pub last_vote_at: Option<Option<DateTime<Utc>>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub give_alert: Option<bool>,
    #[serde(
        default,
        deserialize_with = "crate::common::serde_helpers::deserialize_maybe_undefined",
        skip_serializing_if = "Option::is_none"
    )]
    pub shield_pearl_activated_at: Option<Option<DateTime<Utc>>>,
    #[serde(
        default,
        deserialize_with = "crate::common::serde_helpers::deserialize_maybe_undefined",
        skip_serializing_if = "Option::is_none"
    )]
    pub last_daily_quest_reroll: Option<Option<DateTime<Utc>>>,
}

pub async fn partial_update_user(
    db: &mut PgConnection,
    user_id: &Xid,
    update_data: &UserUpdateData,
) -> Result<Option<User>, sqlx::Error> {
    sqlx::query_as!(
        User,
        r#"
            UPDATE users
            SET
                discord_id = CASE
                    WHEN $2 ? 'discord_id'
                    THEN ($2->>'discord_id')::BIGINT
                    ELSE discord_id END,
                banned = CASE
                    WHEN $2 ? 'banned'
                    THEN ($2->>'banned')::BOOLEAN
                    ELSE banned END,
                emeralds = CASE
                    WHEN $2 ? 'emeralds'
                    THEN ($2->>'emeralds')::BIGINT
                    ELSE emeralds END,
                vault_balance = CASE
                    WHEN $2 ? 'vault_balance'
                    THEN ($2->>'vault_balance')::INTEGER
                    ELSE vault_balance END,
                vault_max = CASE
                    WHEN $2 ? 'vault_max'
                    THEN ($2->>'vault_max')::INTEGER
                    ELSE vault_max END,
                health = CASE
                    WHEN $2 ? 'health'
                    THEN ($2->>'health')::SMALLINT
                    ELSE health END,
                vote_streak = CASE
                    WHEN $2 ? 'vote_streak'
                    THEN ($2->>'vote_streak')::INTEGER
                    ELSE vote_streak END,
                last_vote_at = CASE
                    WHEN $2 ? 'last_vote_at'
                    THEN ($2->>'last_vote_at')::TIMESTAMPTZ
                    ELSE last_vote_at END,
                give_alert = CASE
                    WHEN $2 ? 'give_alert'
                    THEN ($2->>'give_alert')::BOOLEAN
                    ELSE give_alert END,
                shield_pearl_activated_at = CASE
                    WHEN $2 ? 'shield_pearl_activated_at'
                    THEN ($2->>'shield_pearl_activated_at')::TIMESTAMPTZ
                    ELSE shield_pearl_activated_at END,
                last_daily_quest_reroll = CASE
                    WHEN $2 ? 'last_daily_quest_reroll'
                    THEN ($2->>'last_daily_quest_reroll')::TIMESTAMPTZ
                    ELSE last_daily_quest_reroll END,
                modified_at = NOW()
            WHERE id = $1
            RETURNING
                id, discord_id, banned, emeralds, vault_balance, vault_max, health, vote_streak, last_vote_at,
                give_alert, shield_pearl_activated_at, last_daily_quest_reroll, modified_at
        "#,
        user_id.as_bytes(),
        serde_json::to_value(update_data).unwrap(),
    )
    .fetch_optional(&mut *db)
    .await
}

pub async fn get_user_net_wealth(db: &mut PgConnection, id: &Xid) -> Result<i64, sqlx::Error> {
    let result = sqlx::query!(
        r#"
            SELECT
                ((emeralds + (vault_balance * 9)::BIGINT + SUM(items.sell_price::BIGINT * items.amount::BIGINT)))::BIGINT AS total_wealth
            FROM users
            LEFT JOIN items ON users.id = items.user_id
            WHERE users.id = $1
            GROUP BY users.id
        "#,
        id.as_bytes(),
    ).fetch_optional(&mut *db).await?;

    Ok(result.and_then(|r| r.total_wealth).unwrap_or(0))
}

#[cfg(test)]
mod tests {
    use chrono::{TimeDelta, Utc};

    use crate::common::testing::{CreateTestUser, PgPoolConn, create_test_user};

    use super::*;

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
        assert_eq!(a.shield_pearl_activated_at, b.shield_pearl_activated_at);
        assert_eq!(a.last_daily_quest_reroll, b.last_daily_quest_reroll);
        assert_eq!(a.modified_at, b.modified_at);
    }

    #[sqlx::test]
    async fn test_get_user(mut db: PgPoolConn) {
        let expected_user = create_test_user(&mut db, CreateTestUser::default()).await;
        let user = get_user(&mut db, &UserId::Xid(expected_user.id))
            .await
            .unwrap()
            .unwrap();

        assert_users_eq(user, expected_user);
    }

    #[sqlx::test]
    async fn test_get_user_by_discord_id(mut db: PgPoolConn) {
        let expected_user = create_test_user(&mut db, CreateTestUser::default()).await;

        let user = get_user(&mut db, &UserId::Discord(expected_user.discord_id.unwrap()))
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
        let expected_user = create_test_user(&mut db, CreateTestUser::default()).await;
        let user = get_or_create_user(&mut db, &UserId::Xid(expected_user.id))
            .await
            .unwrap();

        assert_users_eq(user, expected_user);
    }

    #[sqlx::test]
    async fn test_get_or_create_existing_user_from_discord(mut db: PgPoolConn) {
        let expected_user = create_test_user(&mut db, CreateTestUser::default()).await;
        let user = get_or_create_user(&mut db, &UserId::Discord(expected_user.discord_id.unwrap()))
            .await
            .unwrap();

        assert_users_eq(user, expected_user);
    }

    #[sqlx::test]
    async fn test_partial_update_whole_user(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        let the_future = Utc::now() + TimeDelta::hours(420);

        let updated_user = partial_update_user(
            &mut db,
            &user.id,
            &UserUpdateData {
                discord_id: Some(Some(1196838524293488662)),
                banned: Some(false),
                emeralds: Some(696969),
                vault_balance: Some(423),
                vault_max: Some(1024),
                health: Some(14),
                vote_streak: Some(153),
                last_vote_at: Some(Some(the_future)),
                give_alert: Some(true),
                shield_pearl_activated_at: Some(Some(the_future)),
                last_daily_quest_reroll: Some(Some(the_future)),
            },
        )
        .await
        .unwrap()
        .unwrap();

        assert_eq!(updated_user.discord_id, Some(1196838524293488662));
        assert_ne!(updated_user.discord_id, user.discord_id);

        assert!(!updated_user.banned);
        assert_ne!(updated_user.banned, user.banned);

        assert_eq!(updated_user.emeralds, 696969);
        assert_ne!(updated_user.emeralds, user.emeralds);

        assert_eq!(updated_user.vault_balance, 423);
        assert_ne!(updated_user.vault_balance, user.vault_balance);

        assert_eq!(updated_user.vault_max, 1024);
        assert_ne!(updated_user.vault_max, user.vault_max);

        assert_eq!(updated_user.health, 14);
        assert_ne!(updated_user.health, user.health);

        assert_eq!(updated_user.vote_streak, 153);
        assert_ne!(updated_user.vote_streak, user.vote_streak);

        assert_eq!(updated_user.last_vote_at, Some(the_future));
        assert_ne!(updated_user.last_vote_at, user.last_vote_at);

        assert!(updated_user.give_alert);
        assert_ne!(updated_user.give_alert, user.give_alert);

        assert_eq!(updated_user.shield_pearl_activated_at, Some(the_future));
        assert_ne!(
            updated_user.shield_pearl_activated_at,
            user.shield_pearl_activated_at
        );

        assert_eq!(updated_user.last_daily_quest_reroll, Some(the_future));
        assert_ne!(
            updated_user.last_daily_quest_reroll,
            user.last_daily_quest_reroll
        );

        assert!(updated_user.modified_at > user.modified_at);
    }

    #[sqlx::test]
    async fn test_partial_update_set_nullable_fields_to_null(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        let updated_user = partial_update_user(
            &mut db,
            &user.id,
            &UserUpdateData {
                discord_id: Some(None),
                banned: Some(false),
                emeralds: Some(696969),
                vault_balance: Some(423),
                vault_max: Some(1024),
                health: Some(14),
                vote_streak: Some(153),
                last_vote_at: Some(None),
                give_alert: Some(true),
                shield_pearl_activated_at: Some(None),
                last_daily_quest_reroll: Some(None),
            },
        )
        .await
        .unwrap()
        .unwrap();

        assert_eq!(updated_user.discord_id, None);
        assert_ne!(updated_user.discord_id, user.discord_id);

        assert!(!updated_user.banned);
        assert_ne!(updated_user.banned, user.banned);

        assert_eq!(updated_user.emeralds, 696969);
        assert_ne!(updated_user.emeralds, user.emeralds);

        assert_eq!(updated_user.vault_balance, 423);
        assert_ne!(updated_user.vault_balance, user.vault_balance);

        assert_eq!(updated_user.vault_max, 1024);
        assert_ne!(updated_user.vault_max, user.vault_max);

        assert_eq!(updated_user.health, 14);
        assert_ne!(updated_user.health, user.health);

        assert_eq!(updated_user.vote_streak, 153);
        assert_ne!(updated_user.vote_streak, user.vote_streak);

        assert_eq!(updated_user.last_vote_at, None);
        assert_ne!(updated_user.last_vote_at, user.last_vote_at);

        assert!(updated_user.give_alert);
        assert_ne!(updated_user.give_alert, user.give_alert);

        assert_eq!(updated_user.shield_pearl_activated_at, None);
        assert_ne!(
            updated_user.shield_pearl_activated_at,
            user.shield_pearl_activated_at
        );

        assert_eq!(updated_user.last_daily_quest_reroll, None);
        assert_ne!(
            updated_user.last_daily_quest_reroll,
            user.last_daily_quest_reroll
        );

        assert!(updated_user.modified_at > user.modified_at);
    }

    #[sqlx::test]
    async fn test_partial_update_nonexistent_user(mut db: PgPoolConn) {
        let updated_user = partial_update_user(
            &mut db,
            &Xid::new(),
            &UserUpdateData {
                discord_id: Some(None),
                banned: Some(false),
                emeralds: Some(696969),
                vault_balance: Some(423),
                vault_max: Some(1024),
                health: Some(14),
                vote_streak: Some(153),
                last_vote_at: Some(None),
                give_alert: Some(true),
                shield_pearl_activated_at: Some(None),
                last_daily_quest_reroll: Some(None),
            },
        )
        .await
        .unwrap();

        assert!(updated_user.is_none());
    }

    #[sqlx::test]
    async fn test_partial_update_user_missing_all_fields(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        let updated_user = partial_update_user(&mut db, &user.id, &UserUpdateData::default())
            .await
            .unwrap()
            .unwrap();

        assert_eq!(updated_user.id, user.id);
        assert_eq!(updated_user.discord_id, user.discord_id);
        assert_eq!(updated_user.banned, user.banned);
        assert_eq!(updated_user.emeralds, user.emeralds);
        assert_eq!(updated_user.vault_balance, user.vault_balance);
        assert_eq!(updated_user.vault_max, user.vault_max);
        assert_eq!(updated_user.health, user.health);
        assert_eq!(updated_user.vote_streak, user.vote_streak);
        assert_eq!(updated_user.last_vote_at, user.last_vote_at);
        assert_eq!(updated_user.give_alert, user.give_alert);
        assert_eq!(
            updated_user.shield_pearl_activated_at,
            user.shield_pearl_activated_at
        );
        assert_eq!(
            updated_user.last_daily_quest_reroll,
            user.last_daily_quest_reroll
        );
    }

    #[sqlx::test]
    async fn test_partial_update_user_only_one_field(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        let updated_user = partial_update_user(
            &mut db,
            &user.id,
            &UserUpdateData {
                discord_id: Some(Some(1234567890)),
                ..UserUpdateData::default()
            },
        )
        .await
        .unwrap()
        .unwrap();

        assert_eq!(updated_user.id, user.id);
        assert_ne!(updated_user.discord_id, user.discord_id);
        assert_eq!(updated_user.banned, user.banned);
        assert_eq!(updated_user.emeralds, user.emeralds);
        assert_eq!(updated_user.vault_balance, user.vault_balance);
        assert_eq!(updated_user.vault_max, user.vault_max);
        assert_eq!(updated_user.health, user.health);
        assert_eq!(updated_user.vote_streak, user.vote_streak);
        assert_eq!(updated_user.last_vote_at, user.last_vote_at);
        assert_eq!(updated_user.give_alert, user.give_alert);
        assert_eq!(
            updated_user.shield_pearl_activated_at,
            user.shield_pearl_activated_at
        );
        assert_eq!(
            updated_user.last_daily_quest_reroll,
            user.last_daily_quest_reroll
        );
    }
}
