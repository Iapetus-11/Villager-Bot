use poem::{Route, post};

mod command_cooldowns;
mod command_executions;
mod commands;

pub fn routes() -> Route {
    Route::new()
        .nest("/commands/", commands::routes())
        .at("/command_cooldowns/check/", post(command_cooldowns::check))
        .at("/command_executions/log/", post(command_executions::log))
}
