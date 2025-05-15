use poem::{Route, get};

mod user;

pub fn routes() -> Route {
    Route::new().at("/:id/", get(user::get_details))
}
