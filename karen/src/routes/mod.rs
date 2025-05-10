use poem::{Route, get};
use users::get_user_details;
mod discord;
mod game;
mod users;

pub fn setup_routes() -> Route {
    Route::new()
        .at("/users/:id/", get(get_user_details))
        .nest("/discord/", discord::routes())
        .nest("/game/", game::routes())
}
