use poem::http::StatusCode;
use subtle::ConstantTimeEq;

use crate::config::Config;

pub struct RequireAuthedClient;

impl<'a> poem::FromRequest<'a> for RequireAuthedClient {
    async fn from_request(
        req: &'a poem::Request,
        _body: &mut poem::RequestBody,
    ) -> poem::Result<Self> {
        let config = req.data::<Config>().unwrap();

        let authorization_header = req.header("Authorization").unwrap_or("");

        if authorization_header.is_empty() {
            return Err(poem::Error::from_string(
                "missing authorization header",
                StatusCode::UNAUTHORIZED,
            ));
        }

        // TODO: Use constant time comparison here
        if !bool::from(
            authorization_header
                .as_bytes()
                .ct_eq(format!("Token {}", config.auth_token).as_bytes()),
        ) {
            return Err(poem::Error::from_string(
                "incorrect authorization header",
                StatusCode::UNAUTHORIZED,
            ));
        }

        Ok(RequireAuthedClient)
    }
}
