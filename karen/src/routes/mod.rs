use poem::{Route, post};

mod command_executions;
mod commands;
mod discord;
mod users;

pub fn setup_routes() -> Route {
    Route::new()
        .nest("/discord/", discord::routes())
        .nest("/users/", users::routes())
        .nest("/commands/", commands::routes())
        .at(
            "/command_executions/preflight/",
            post(command_executions::preflight),
        )
}
