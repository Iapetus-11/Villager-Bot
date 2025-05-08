use sqlx::PgConnection;

use crate::models::db::DiscordGuild;

pub async fn get_discord_guild(
    db: &mut PgConnection,
    id: i64,
) -> Result<Option<DiscordGuild>, sqlx::Error> {
    sqlx::query_as!(
        DiscordGuild,
        r#"
            SELECT
                id, prefix, language, mc_server, silly_triggers, disabled_commands
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
                INSERT INTO discord_guilds (id, prefix, language)
                VALUES ($1, $2, $3)
                RETURNING id, prefix, language, mc_server, silly_triggers, disabled_commands
            "#,
            id,
            "!!", // TODO: Load default prefix from config?
            "en", // TODO: Infer language from guild settings or default from config?
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

#[cfg(test)]
mod tests {
    use super::*;

    use crate::common::testing::{PgPoolConn, TestDiscordGuild, create_test_discord_guild};

    fn assert_discord_guilds_eq(a: &DiscordGuild, b: &DiscordGuild) {
        assert_eq!(a.id, b.id);
        assert_eq!(a.prefix, b.prefix);
        assert_eq!(a.language, b.language);
        assert_eq!(a.mc_server, b.mc_server);
        assert_eq!(a.silly_triggers, b.silly_triggers);
        assert_eq!(a.disabled_commands, b.disabled_commands);
    }

    #[sqlx::test]
    async fn test_get_discord_guild(mut db: PgPoolConn) {
        let expected_discord_guild =
            create_test_discord_guild(&mut db, TestDiscordGuild::default()).await;
        create_test_discord_guild(
            &mut db,
            TestDiscordGuild {
                id: 841092817471537152,
                ..TestDiscordGuild::default()
            },
        )
        .await;

        let discord_guild = get_discord_guild(&mut db, expected_discord_guild.id)
            .await
            .unwrap()
            .unwrap();

        assert_discord_guilds_eq(&expected_discord_guild, &discord_guild);
    }

    #[sqlx::test]
    async fn test_get_nonexistent_discord_guild(mut db: PgPoolConn) {
        let result = get_discord_guild(&mut db, 386585461285715968)
            .await
            .unwrap();
        assert!(result.is_none());
    }

    #[sqlx::test]
    async fn test_get_or_create_existing_discord_guild(mut db: PgPoolConn) {
        let expected_discord_guild =
            create_test_discord_guild(&mut db, TestDiscordGuild::default()).await;
        create_test_discord_guild(
            &mut db,
            TestDiscordGuild {
                id: 841092817471537152,
                ..TestDiscordGuild::default()
            },
        )
        .await;

        let discord_guild = get_or_create_discord_guild(&mut db, expected_discord_guild.id)
            .await
            .unwrap();

        assert_discord_guilds_eq(&discord_guild, &expected_discord_guild);
    }

    #[sqlx::test]
    async fn test_get_or_create_nonexistent_discord_guild(mut db: PgPoolConn) {
        create_test_discord_guild(&mut db, TestDiscordGuild::default()).await;
        create_test_discord_guild(
            &mut db,
            TestDiscordGuild {
                id: 841092817471537152,
                ..TestDiscordGuild::default()
            },
        )
        .await;

        let discord_guild = get_or_create_discord_guild(&mut db, 386585461285715968)
            .await
            .unwrap();

        assert_eq!(discord_guild.id, 386585461285715968);

        // Assert defaults
        assert_eq!(discord_guild.prefix, "!!");
        assert_eq!(discord_guild.language, "en");
        assert_eq!(discord_guild.mc_server, None);
        assert!(discord_guild.silly_triggers);
        assert_eq!(discord_guild.disabled_commands, Vec::<String>::new());
    }
}
