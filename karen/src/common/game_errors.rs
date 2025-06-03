use std::fmt::Debug;

use poem::{Body, IntoResponse, Response, http::StatusCode};

/// Common game/economy errors that are used within many endpoints
#[derive(Debug, thiserror::Error, serde::Serialize)]
#[cfg_attr(test, derive(serde::Deserialize))]
#[serde(tag = "error_type")]
pub enum GameError {
    #[error("User does not exist")]
    UserDoesNotExist,

    #[error("User lock {:#?} cannot be acquired", .lock)]
    UserLockCannotBeAcquired { lock: String },

    #[error("User does not have enough emeralds")]
    NotEnoughEmeralds,
}

impl From<GameError> for poem::Error {
    fn from(value: GameError) -> Self {
        let status_code = match value {
            GameError::UserDoesNotExist => StatusCode::NOT_FOUND,
            GameError::UserLockCannotBeAcquired { .. } => StatusCode::CONFLICT,
            GameError::NotEnoughEmeralds => StatusCode::BAD_REQUEST,
        };

        poem::Error::from_response(
            Response::builder()
                .status(status_code)
                .body(Body::from_json(value).unwrap())
                .with_content_type("application/json")
                .into_response(),
        )
    }
}
