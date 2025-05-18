use std::{
    str::FromStr,
    sync::{Arc, LazyLock, OnceLock},
};

use poem::{
    Endpoint, EndpointExt, Middleware,
    endpoint::BoxEndpoint,
    http::{HeaderName, HeaderValue},
    middleware::{AddData, CatchPanic, NormalizePath, TrailingSlash},
    test::TestClient,
};

use crate::{config::Config, routes};

pub static TEST_CONFIG: LazyLock<Config> = LazyLock::new(|| Config {
    database_url: "postgresql://test_user:password@example.com/villager-bot".to_string(),
    database_pool_size: 0,
    server_host_address: "http://127.0.0.1:-1".to_string(),
    auth_token: "AUTH-TOKEN".to_string(),
});

// Cache API test client to improve test execution speed
static TEST_API_INSTANCE: OnceLock<Arc<BoxEndpoint<'static>>> = OnceLock::new();

struct SetRequestHeaderMiddlewareImpl<E> {
    ep: E,

    header: String,
    header_value: String,
}

impl<E: Endpoint> Endpoint for SetRequestHeaderMiddlewareImpl<E> {
    type Output = E::Output;

    async fn call(&self, mut req: poem::Request) -> poem::Result<Self::Output> {
        if req.header(&self.header).is_none() {
            req.headers_mut().append(
                HeaderName::from_str(&self.header).unwrap(),
                HeaderValue::from_str(&self.header_value).unwrap(),
            );
        }

        self.ep.call(req).await
    }
}

struct SetRequestHeaderMiddleware {
    header: String,
    header_value: String,
}

impl SetRequestHeaderMiddleware {
    pub fn new(header: impl Into<String>, header_value: impl Into<String>) -> Self {
        Self {
            header: header.into(),
            header_value: header_value.into(),
        }
    }
}

impl<E: Endpoint> Middleware<E> for SetRequestHeaderMiddleware {
    type Output = SetRequestHeaderMiddlewareImpl<E>;

    fn transform(&self, ep: E) -> Self::Output {
        SetRequestHeaderMiddlewareImpl {
            ep,
            header: self.header.clone(),
            header_value: self.header_value.clone(),
        }
    }
}

pub fn setup_api_test_client(db_pool: sqlx::PgPool) -> TestClient<BoxEndpoint<'static>> {
    let cached_app = TEST_API_INSTANCE.get_or_init(|| {
        let app = routes::setup_routes()
            .with(NormalizePath::new(TrailingSlash::Always))
            .with(AddData::new(Arc::new(TEST_CONFIG.clone())))
            .with(SetRequestHeaderMiddleware::new(
                "Authorization",
                format!("Bearer {}", TEST_CONFIG.auth_token),
            ))
            .with(CatchPanic::new());

        Arc::new(app.boxed())
    });

    // I do not know exactly what #[sqlx::test] does under the hood, specifically if they reuse db pools between tests,
    // either way I want to be safe.
    TestClient::new(cached_app.clone().with(AddData::new(db_pool)).boxed())
}
