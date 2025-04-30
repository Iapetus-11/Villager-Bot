use crate::{
    common::{user_id::UserId, xid::Xid},
    models::User,
};

pub async fn get_user(
    db: &sqlx::Pool<sqlx::Postgres>,
    id: &UserId,
) -> Result<Option<User>, sqlx::Error> {
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
        ).fetch_optional(db).await,
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
        ).fetch_optional(db).await
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
    db: &sqlx::Pool<sqlx::Postgres>,
    id: &UserId,
) -> Result<User, GetOrCreateUserError> {
    let mut user = get_user(db, id)
        .await
        .map_err(GetOrCreateUserError::Database)?;

    if user.is_none() {
        let creation_result = match id {
            UserId::Xid(_) => Err(GetOrCreateUserError::CannotCreateUsingXid),
            UserId::Discord(discord_id) => {
                let id = Xid::new();

                // TODO: Ensure starter items

                sqlx::query_as!(
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
                ).fetch_one(db).await.map_err(GetOrCreateUserError::Database)
            }
        };

        user = Some(match creation_result {
            Ok(discord_guild) => Ok(discord_guild),
            Err(GetOrCreateUserError::Database(sqlx::Error::Database(error)))
                if error.is_unique_violation() =>
            {
                get_user(db, id)
                    .await
                    .map(|u| u.unwrap())
                    .map_err(GetOrCreateUserError::Database)
            }
            error => error,
        }?);
    }

    Ok(user.unwrap())
}
