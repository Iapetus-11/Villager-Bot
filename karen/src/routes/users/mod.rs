use poem::{Route, get};

mod badges;
mod user;

pub fn routes() -> Route {
    Route::new()
        .at("/:id/", get(user::get_details))
        .at("/:id/badges/image", get(badges::get_image))
}
