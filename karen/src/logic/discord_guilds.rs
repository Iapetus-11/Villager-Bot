use sqlx::PgConnection;

use crate::models::DiscordGuild;

pub async fn get_discord_guild(
    db: &mut PgConnection,
    id: i64,
) -> Result<Option<DiscordGuild>, sqlx::Error> {
    sqlx::query_as!(
        DiscordGuild,
        r#"
            SELECT
                id, prefix, language, mc_server, silly_triggers
            FROM discord_guilds
            WHERE id = $1
        "#,
        id,
    )
    .fetch_optional(&mut *db)
    .await
}

pub async fn get_or_create_discord_guild(
    db: &mut PgConnection,
    id: i64,
) -> Result<DiscordGuild, sqlx::Error> {
    let mut discord_guild = get_discord_guild(&mut *db, id).await?;

    if discord_guild.is_none() {
        let creation_result = sqlx::query_as!(
            DiscordGuild,
            r#"
                INSERT INTO discord_guilds (id, prefix)
                VALUES ($1, $2)
                RETURNING id, prefix, language, mc_server, silly_triggers
            "#,
            id,
            "!!" // TODO: Load default prefix from config?
        )
        .fetch_one(&mut *db)
        .await;

        discord_guild = Some(match creation_result {
            Ok(discord_guild) => Ok(discord_guild),
            Err(sqlx::Error::Database(error)) if error.is_unique_violation() => {
                get_discord_guild(&mut *db, id).await.map(|dg| dg.unwrap())
            }
            error => error,
        }?);
    }

    Ok(discord_guild.unwrap())
}
