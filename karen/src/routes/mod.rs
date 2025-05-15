use poem::Route;
mod discord;
mod game;
mod users;

pub fn setup_routes() -> Route {
    Route::new()
        .nest("/users/", users::routes())
        .nest("/discord/", discord::routes())
        .nest("/game/", game::routes())
}
