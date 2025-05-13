use ::serde::{Deserialize, Serialize};
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

#[derive(Serialize, Deserialize)]
pub struct DiscordGuildUpdateData {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    prefix: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    language: Option<String>,
    #[serde(
        default,
        deserialize_with = "crate::common::serde_helpers::deserialize_maybe_undefined",
        skip_serializing_if = "Option::is_none"
    )]
    mc_server: Option<Option<String>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    silly_triggers: Option<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    disabled_commands: Option<Vec<String>>,
}

/// Update (potentially partially) a DiscordGuild, leave fields as None to exclude them from the update query.
pub async fn partial_update_discord_guild(
    db: &mut PgConnection,
    guild_id: i64,
    update_data: &DiscordGuildUpdateData,
) -> Result<Option<DiscordGuild>, sqlx::Error> {
    sqlx::query_as!(
        DiscordGuild,
        r#"
            UPDATE discord_guilds
            SET
                prefix = CASE 
                    WHEN $2 ? 'prefix' 
                    THEN ($2->>'prefix')::VARCHAR 
                    ELSE prefix END,
                language = CASE
                    WHEN $2 ? 'language' 
                    THEN ($2->>'language')::VARCHAR 
                    ELSE language END,
                mc_server = CASE
                    WHEN $2 ? 'mc_server'
                    THEN ($2->>'mc_server')::VARCHAR
                    ELSE mc_server END,
                silly_triggers = CASE
                    WHEN $2 ? 'silly_triggers'
                    THEN ($2->>'silly_triggers')::BOOLEAN
                    ELSE silly_triggers END,
                disabled_commands = CASE
                    WHEN $2 ? 'disabled_commands'
                    THEN (SELECT ARRAY_AGG(json_disabled_commands) FROM JSONB_ARRAY_ELEMENTS_TEXT($2->'disabled_commands') AS json_disabled_commands)
                    ELSE disabled_commands END
            WHERE id = $1
            RETURNING id, prefix, language, mc_server, silly_triggers, disabled_commands
        "#,
        guild_id,
        serde_json::to_value(update_data).unwrap(),
    )
    .fetch_optional(&mut *db)
    .await
}

#[cfg(test)]
mod tests {
    use super::*;

    use crate::common::testing::{CreateTestDiscordGuild, PgPoolConn, create_test_discord_guild};

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
            create_test_discord_guild(&mut db, CreateTestDiscordGuild::default()).await;
        create_test_discord_guild(
            &mut db,
            CreateTestDiscordGuild {
                id: 841092817471537152,
                ..CreateTestDiscordGuild::default()
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
            create_test_discord_guild(&mut db, CreateTestDiscordGuild::default()).await;
        create_test_discord_guild(
            &mut db,
            CreateTestDiscordGuild {
                id: 841092817471537152,
                ..CreateTestDiscordGuild::default()
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
        create_test_discord_guild(&mut db, CreateTestDiscordGuild::default()).await;
        create_test_discord_guild(
            &mut db,
            CreateTestDiscordGuild {
                id: 841092817471537152,
                ..CreateTestDiscordGuild::default()
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

    #[sqlx::test]
    async fn test_partial_update_whole_guild(mut db: PgPoolConn) {
        let discord_guild = create_test_discord_guild(&mut db, Default::default()).await;

        let updated_discord_guild = partial_update_discord_guild(
            &mut db,
            discord_guild.id,
            &DiscordGuildUpdateData {
                prefix: Some("//".to_string()),
                language: Some("fr".to_string()),
                mc_server: Some(Some("xenon.iapetus11.me".to_string())),
                silly_triggers: Some(false),
                disabled_commands: Some(vec!["help".to_string(), "mine".to_string()]),
            },
        )
        .await
        .unwrap()
        .unwrap();

        assert_eq!(updated_discord_guild.prefix, "//");
        assert_ne!(discord_guild.prefix, updated_discord_guild.prefix);

        assert_eq!(updated_discord_guild.language, "fr");
        assert_ne!(discord_guild.language, updated_discord_guild.language);

        assert_eq!(
            updated_discord_guild.mc_server,
            Some("xenon.iapetus11.me".to_string())
        );
        assert_ne!(discord_guild.mc_server, updated_discord_guild.mc_server);

        assert!(!updated_discord_guild.silly_triggers);
        assert_ne!(
            discord_guild.silly_triggers,
            updated_discord_guild.silly_triggers
        );

        assert_eq!(
            updated_discord_guild.disabled_commands,
            vec!["help".to_string(), "mine".to_string()]
        );
        assert_ne!(
            discord_guild.disabled_commands,
            updated_discord_guild.disabled_commands
        );
    }

    #[sqlx::test]
    async fn test_partial_update_nonexistent_guild(mut db: PgPoolConn) {
        let updated_discord_guild = partial_update_discord_guild(
            &mut db,
            123123123123123123_i64,
            &DiscordGuildUpdateData {
                prefix: Some("//".to_string()),
                language: None,
                mc_server: None,
                silly_triggers: None,
                disabled_commands: None,
            },
        )
        .await
        .unwrap();

        assert!(updated_discord_guild.is_none());
    }

    #[sqlx::test]
    async fn test_partial_update_missing_all_fields(mut db: PgPoolConn) {
        let discord_guild = create_test_discord_guild(&mut db, Default::default()).await;

        let updated_discord_guild = partial_update_discord_guild(
            &mut db,
            discord_guild.id,
            &DiscordGuildUpdateData {
                prefix: None,
                language: None,
                mc_server: None,
                silly_triggers: None,
                disabled_commands: None,
            },
        )
        .await
        .unwrap()
        .unwrap();

        assert_discord_guilds_eq(&discord_guild, &updated_discord_guild);
    }

    #[sqlx::test]
    async fn test_partial_update_only_one_field(mut db: PgPoolConn) {
        let discord_guild = create_test_discord_guild(&mut db, Default::default()).await;

        let updated_discord_guild = partial_update_discord_guild(
            &mut db,
            discord_guild.id,
            &DiscordGuildUpdateData {
                prefix: None,
                language: None,
                mc_server: None,
                silly_triggers: None,
                disabled_commands: Some(vec!["balls".to_string(), "test".to_string()]),
            },
        )
        .await
        .unwrap()
        .unwrap();

        assert_eq!(discord_guild.id, updated_discord_guild.id);
        assert_eq!(discord_guild.prefix, updated_discord_guild.prefix);
        assert_eq!(discord_guild.language, updated_discord_guild.language);
        assert_eq!(discord_guild.mc_server, updated_discord_guild.mc_server);
        assert_eq!(
            discord_guild.silly_triggers,
            updated_discord_guild.silly_triggers
        );

        assert_eq!(
            updated_discord_guild.disabled_commands,
            vec!["balls".to_string(), "test".to_string()]
        );
        assert_ne!(
            discord_guild.disabled_commands,
            updated_discord_guild.disabled_commands
        );
    }
}
