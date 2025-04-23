use std::error::Error as StdError;

use poem::{
    EndpointExt, Server,
    listener::TcpListener,
    middleware::{AddData, CatchPanic, NormalizePath, TrailingSlash},
};

mod common;
mod config;
mod models;
mod routes;

#[tokio::main]
async fn main() -> Result<(), Box<dyn StdError>> {
    let config = config::load();

    let db_pool = sqlx::postgres::PgPoolOptions::new()
        .max_connections(config.database_pool_size)
        .connect(&config.database_url)
        .await?;

    let routes = routes::setup_routes()
        .with(NormalizePath::new(TrailingSlash::Always))
        .with(AddData::new(config.clone()))
        .with(AddData::new(db_pool.clone()))
        .with(CatchPanic::new());

    println!(
        "Starting server on http://{0} ...",
        config.server_host_address
    );

    Server::new(TcpListener::bind(config.server_host_address))
        .run(routes)
        .await?;

    Ok(())
}
