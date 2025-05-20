use std::{env, error::Error as StdError, sync::Arc};

use poem::{
    listener::TcpListener, middleware::{AddData, CatchPanic, NormalizePath, Tracing, TrailingSlash}, EndpointExt, Server
};
use thiserror::Error;

mod common;
mod config;
mod logic;
mod models;
mod routes;

#[derive(Debug, Error)]
pub enum CliError {
    #[error("{:#?} is not a valid command, must be one of: api", .0)]
    UnknownCommand(String),

    #[error("You must specify a command that is one of: api")]
    MissingCommand,
}

async fn run_api() -> Result<(), Box<dyn StdError>> {
    let config = Arc::new(config::load());

    let db_pool = sqlx::postgres::PgPoolOptions::new()
        .max_connections(config.database_pool_size)
        .connect(&config.database_url)
        .await?;

    let app = routes::setup_routes()
        .with(Tracing)
        .with(NormalizePath::new(TrailingSlash::Always))
        .with(AddData::new(config.clone()))
        .with(AddData::new(db_pool.clone()))
        .with(CatchPanic::new());

    Server::new(TcpListener::bind(config.server_host_address.clone()))
        .run(app)
        .await?;

    Ok(())
}

#[tokio::main]
async fn main() {
    tracing::subscriber::set_global_default(tracing_subscriber::FmtSubscriber::new()).unwrap();

    let mut args = env::args().skip(1);
    let command = args.next().unwrap_or("".into());
    let _args = args.collect::<Vec<_>>();

    let result = match command.as_str() {
        "api" => run_api().await,
        "" => Err(CliError::MissingCommand.into()),
        unknown_command => Err(CliError::UnknownCommand(unknown_command.to_string()).into()),
    };

    match result {
        Ok(_) => {}
        Err(error) => {
            eprintln!("An error occurred while running {:#?}:\n{}", command, error);
        }
    }
}
