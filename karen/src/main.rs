use std::{error::Error as StdError, sync::Arc};

use models::data;
use poem::{
    EndpointExt, Server,
    listener::TcpListener,
    middleware::{AddData, CatchPanic, NormalizePath, TrailingSlash},
};

mod common;
mod config;
mod logic;
mod models;
mod routes;
mod utils;

#[tokio::main]
async fn main() -> Result<(), Box<dyn StdError>> {
    let config = Arc::new(config::load());

    let items_data = Arc::new(data::items::load()?);

    let db_pool = sqlx::postgres::PgPoolOptions::new()
        .max_connections(config.database_pool_size)
        .connect(&config.database_url)
        .await?;

    let app = routes::setup_routes()
        .with(NormalizePath::new(TrailingSlash::Always))
        .with(AddData::new(config.clone()))
        .with(AddData::new(db_pool.clone()))
        .with(AddData::new(items_data))
        .with(CatchPanic::new());

    println!(
        "Starting server on http://{0} ...",
        config.server_host_address
    );

    Server::new(TcpListener::bind(config.server_host_address.clone()))
        .run(app)
        .await?;

    Ok(())
}
