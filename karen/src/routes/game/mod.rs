use badges::get_user_badges_image;
use cooldowns::check_cooldown;
use poem::{Route, get, post};

mod badges;
mod cooldowns;

pub fn routes() -> Route {
    Route::new()
        .at("/cooldowns/check/", post(check_cooldown))
        .at("/badges/:user_id/", get(get_user_badges_image))
}
