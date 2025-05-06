use poem::{IntoEndpoint, Route, get};
use users::get_user_details;
mod discord;
mod game;
mod users;

pub fn setup_routes() -> Route {
    Route::new()
        .at("/users/:id/", get(get_user_details))
        .at("/discord/", discord::routes().into_endpoint())
        .at("/game/", game::routes().into_endpoint())
}
