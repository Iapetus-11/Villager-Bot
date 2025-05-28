use poem::{Route, get, post};

mod profile;
mod vault;

pub fn routes() -> Route {
    Route::new()
        .at("/profile/:user_id/", get(profile::get_data))
        .at("/vault/:user_id/deposit/", post(vault::deposit))
        .at("/vault/:user_id/withdraw/", post(vault::withdraw))
}
