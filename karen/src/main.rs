use std::{env, error::Error as StdError, sync::Arc};

use config::Config;
use logic::check_data::check_items_data;
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
    #[error("{:#?} is not a valid command, must be one of: api", .0)]
    UnknownCommand(String),

    #[error("You must specify a command that is one of: api")]
    MissingCommand,
}

async fn run_api() -> Result<(), Box<dyn StdError>> {
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

fn check_data() -> Result<(), Box<dyn StdError>> {
    let items_data = data::items::load()?;
    check_items_data(&items_data)?;

    Ok(())
}

#[tokio::main]
async fn main() {
    let mut args =  env::args().skip(1);
    let command = args.next().unwrap_or("".into());
    let _args = args.collect::<Vec<_>>();

    let result = match command.as_str() {
        "api" => run_api().await,
        "check" => check_data(),
        "" => Err(CliError::MissingCommand.into()),
        unknown_command => Err(CliError::UnknownCommand(unknown_command.to_string()).into()),
    };

    match result {
        Ok(_) => {},
        Err(error) => {
            eprintln!("An error occurred while running {:#?}:\n{}", command, error);
        }
    }
}
