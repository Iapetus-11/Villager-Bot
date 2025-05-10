use std::fmt::Debug;

use poem::{error::ResponseError, http::StatusCode};

#[derive(Debug, thiserror::Error)]
#[error("Forbidden")]
pub struct ForbiddenError;

impl ResponseError for ForbiddenError {
    fn status(&self) -> StatusCode {
        StatusCode::FORBIDDEN
    }
}
