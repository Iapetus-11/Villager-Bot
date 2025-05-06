use cooldowns::check_cooldown;
use poem::{Route, post};

mod cooldowns;

pub fn routes() -> Route {
    Route::new().at("/cooldowns/check/", post(check_cooldown))
}
