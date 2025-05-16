use cooldowns::check_cooldown;
use poem::{Route, post};

mod commands;
mod cooldowns;

pub fn routes() -> Route {
    Route::new()
        .nest("/commands/", commands::routes())
        .at("/cooldowns/check/", post(check_cooldown))
}
