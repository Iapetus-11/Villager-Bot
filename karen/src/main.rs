use std::{env, error::Error as StdError, sync::Arc};

use config::Config;
use models::data::{self, items::ItemsData};
use poem::{
    EndpointExt, Server,
    listener::TcpListener,
    middleware::{AddData, CatchPanic, NormalizePath, TrailingSlash},
};
use thiserror::Error;

mod common;
mod config;
mod logic;
mod models;
mod routes;
mod utils;

#[derive(Debug, Error)]
pub enum CliError {
    #[error("{0:#?} is not a valid command, must be one of: api")]
    UnknownCommand(String),

    #[error("You must specify a command that is one of: api")]
    MissingCommand,
}

async fn run_api(config: Arc<Config>, items_data: Arc<ItemsData>, db_pool: sqlx::Pool<sqlx::Postgres>) -> Result<(), Box<dyn StdError>> {
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

fn run_data_validation() -> Result<(), Box<dyn StdError>> {
    todo!();
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn StdError>> {
    let mut args =  env::args().skip(1);
    let command = args.next();
    let _args = args.collect::<Vec<_>>();

    let config = Arc::new(config::load());

    let items_data = Arc::new(data::items::load()?);

    let db_pool = sqlx::postgres::PgPoolOptions::new()
        .max_connections(config.database_pool_size)
        .connect(&config.database_url)
        .await?;

    match command.unwrap_or("".into()).as_str() {
        "api" => run_api(config, items_data, db_pool).await,
        "" => Err(CliError::MissingCommand.into()),
        unknown_command => Err(CliError::UnknownCommand(unknown_command.to_string()).into()),
    }
}
