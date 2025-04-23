use poem::http::StatusCode;

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
        if authorization_header.len() == 0 {
            return Err(poem::Error::from_string("Missing Authorization header", StatusCode::FORBIDDEN));
        }

        // TODO: Use constant time comparison here
        if authorization_header != format!("Token {}", config.auth_token) {
            return Err(poem::Error::from_string("Incorrect Authorization header", StatusCode::FORBIDDEN))
        }

        Ok(RequireAuthedClient)
    }
}