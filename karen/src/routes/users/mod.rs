use poem::{Route, get};

mod badges;
mod items;
mod user;

pub fn routes() -> Route {
    Route::new()
        .at("/:id/", get(user::get_details))
        .at("/:id/badges/image/", get(badges::get_image))
        .at("/:id/items/", get(items::list))
}
