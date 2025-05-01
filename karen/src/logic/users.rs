use sqlx::Connection;
use sqlx::PgConnection;

use crate::{
    common::{user_id::UserId, xid::Xid},
    models::{Item, User},
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

pub async fn create_default_user_items(db: &mut PgConnection, user_id: Xid) -> Result<(), sqlx::Error> {
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

                create_default_user_items(&mut *tx, id).await.map_err(GetOrCreateUserError::Database)?;

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
