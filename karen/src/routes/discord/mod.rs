use guilds::{get_guild_details, update_guild_details};
use poem::{Route, get};

mod guilds;

pub fn routes() -> Route {
    Route::new().at(
        "/guilds/:id/",
        get(get_guild_details).patch(update_guild_details),
    )
}
