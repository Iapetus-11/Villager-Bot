use sqlx::PgConnection;

use crate::common::xid::Xid;

pub async fn get_active_user_effects(
    db: &mut PgConnection,
    user_id: &Xid,
) -> Result<Vec<String>, sqlx::Error> {
    struct UserEffect {
        name: String,
    }

    let user_effects = sqlx::query_as!(
        UserEffect,
        "SELECT name FROM user_effects WHERE user_id = $1",
        user_id.as_bytes()
    )
    .fetch_all(&mut *db)
    .await?;

    Ok(user_effects.into_iter().map(|uf| uf.name).collect())
}
