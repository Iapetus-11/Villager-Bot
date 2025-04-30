use discord::routes;
use poem::{IntoEndpoint, Route, get};
use users::get_user_details;
mod discord;
mod users;

pub fn setup_routes() -> Route {
    Route::new()
        .at("/users/:id/", get(get_user_details))
        .at("/discord/", routes().into_endpoint())
}
