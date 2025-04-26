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

        // TODO: is 403 forbidden correct here (and on line 24)
        if authorization_header.is_empty() {
            return Err(poem::Error::from_string(
                "missing authorization header",
                StatusCode::FORBIDDEN,
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
                StatusCode::FORBIDDEN,
            ));
        }

        Ok(RequireAuthedClient)
    }
}
