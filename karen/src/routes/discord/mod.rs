use guilds::get_guild_details;
use poem::{get, Route};

pub mod guilds;

pub fn routes() -> Route {
    Route::new()
        .at("/guilds/:id/", get(get_guild_details))
}