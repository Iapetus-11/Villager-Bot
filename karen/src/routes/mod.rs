use poem::{Route, get};
use users::get_user_details;
mod users;

pub fn setup_routes() -> Route {
    Route::new().at("/users/:user_id/", get(get_user_details))
}
