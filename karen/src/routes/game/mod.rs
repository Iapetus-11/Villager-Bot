use poem::{Route, post};

mod command_executions;
mod commands;

pub fn routes() -> Route {
    Route::new().nest("/commands/", commands::routes()).at(
        "/command_executions/preflight/",
        post(command_executions::preflight),
    )
}
