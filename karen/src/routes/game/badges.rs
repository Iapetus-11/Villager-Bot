use poem::{error::NotFoundError, http::StatusCode, web::{Data, Path}};

use crate::{common::{security::RequireAuthedClient, user_id::UserId}, logic::{badges::{generate_user_badges_image, get_user_badges}, users::{get_or_create_user, get_user, GetOrCreateUserError}}};

#[poem::handler]
pub async fn get_user_badges_image(
    db: Data<&sqlx::PgPool>,
    Path((user_id,)): Path<(UserId,)>,
    _: RequireAuthedClient,
) -> Result<poem::Response, poem::Error> {
    let mut db = db.acquire().await.unwrap();

    let user_result = get_or_create_user(&mut *db, &user_id).await;
    if matches!(user_result, Err(GetOrCreateUserError::CannotCreateUsingXid)) {
        return Err(poem::Error::from_string(
            "User does not exist, and cannot create a new one from an Xid",
            StatusCode::BAD_REQUEST,
        ));
    }
    let user = user_result.unwrap();

    let Some(badges) = get_user_badges(&mut *db, &user.id).await.unwrap() else {
        return Err(NotFoundError.into());
    };
    let Some(badges_image_data) = generate_user_badges_image(&badges).await.unwrap() else {
        return Err(NotFoundError.into());
    };

    Ok(poem::Response::builder().content_type("image/png").body(badges_image_data))
}