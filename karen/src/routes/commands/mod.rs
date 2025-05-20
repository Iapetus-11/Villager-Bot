use poem::{Route, get};

mod profile;

pub fn routes() -> Route {
    Route::new().at("/profile/:user_id/", get(profile::get_data))
}
