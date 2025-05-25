use std::{env, error::Error as StdError, sync::Arc};

use chrono::Utc;
use poem::{
    EndpointExt, Server,
    listener::TcpListener,
    middleware::{AddData, CatchPanic, NormalizePath, Tracing, TrailingSlash},
};
use thiserror::Error;
use tokio_schedule::Job;
use tracing::{event, span, Level};

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

async fn setup_recurring_tasks(db_pool: sqlx::Pool<sqlx::Postgres>) {
    let db_pool_c1 = db_pool.clone();
    tokio::spawn(
        tokio_schedule::every(1)
            .hour()
            .in_timezone(&Utc)
            .perform(move || {
                let db_pool = db_pool_c1.clone();

                async move {
                    use logic::items::sync_db_items_from_registry;

                    event!(Level::INFO, "Syncing DB items from item registry...");

                    let mut db = db_pool.acquire().await.unwrap();
                    sync_db_items_from_registry(&mut db).await.unwrap();
                }
            }),
    );

    let db_pool_c2 = db_pool.clone();
    tokio::spawn(
        tokio_schedule::every(12)
            .hours()
            .in_timezone(&Utc)
            .perform(move || {
                let db_pool = db_pool_c2.clone();
                async move {
                    use logic::fishing::randomize_fish_prices;
                    
                    event!(Level::INFO, "Randomizing fish market prices...");

                    let mut db = db_pool.acquire().await.unwrap();
                    randomize_fish_prices(&mut db).await.unwrap();
                }
            }),
    );
}

async fn run_api() -> Result<(), Box<dyn StdError>> {
    let config = Arc::new(config::load());

    let db_pool = sqlx::postgres::PgPoolOptions::new()
        .max_connections(config.database_pool_size)
        .connect(&config.database_url)
        .await?;

    setup_recurring_tasks(db_pool.clone()).await;

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
