use poem::{
    handler,
    web::{Data, Json, Path},
};

use crate::{
    common::user_id::UserId,
    logic::commands::profile::{ProfileCommandData, get_profile_command_data},
};

#[handler]
pub async fn get_data(
    db: Data<&sqlx::PgPool>,
    Path((user_id,)): Path<(UserId,)>,
) -> Result<Json<ProfileCommandData>, poem::Error> {
    let mut db = db.acquire().await.unwrap();

    Ok(Json(
        get_profile_command_data(&mut db, &user_id).await.unwrap(),
    ))
}
