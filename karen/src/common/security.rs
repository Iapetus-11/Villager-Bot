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

        let Some(authorization_header) = req.header("Authorization") else {
            return Err(poem::Error::from_string(
                "missing authorization header",
                StatusCode::UNAUTHORIZED,
            ));
        };

        let Some(authorization_token) = authorization_header.strip_prefix("Bearer ") else {
            return Err(poem::Error::from_string(
                "invalid scheme in authorization header",
                StatusCode::UNAUTHORIZED,
            ));
        };

        if !bool::from(
            authorization_token
                .as_bytes()
                .ct_eq(config.auth_token.as_bytes()),
        ) {
            println!("Here 36");
            return Err(poem::Error::from_string(
                "incorrect authorization header",
                StatusCode::UNAUTHORIZED,
            ));
        }

        Ok(RequireAuthedClient)
    }
}
