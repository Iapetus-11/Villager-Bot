use poem::{Route, post};

mod profile;

pub fn routes() -> Route {
    Route::new().at("/profile/:user_id/", post(profile::get_data))
}
