use poem::{Route, get, post};

mod profile;
mod shop;
mod vault;

pub fn routes() -> Route {
    Route::new()
        .at("/profile/:user_id/", get(profile::get_data))
        // ---
        .at("/vault/:user_id/deposit/", post(vault::deposit))
        .at("/vault/:user_id/withdraw/", post(vault::withdraw))
        // ---
        .at("/shop/items/:category/", get(shop::items_for_category))
}
