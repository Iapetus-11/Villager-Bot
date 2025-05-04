use thiserror::Error;

use crate::models::data::items::ItemsData;

#[derive(Debug, Error)]
pub enum ItemsDataError {
    #[error("The shop item {:#?} was not present in the item registry", .0)]
    ShopItemNotRegistered(String),
}


pub fn check_items_data(data: &ItemsData) -> Result<(), ItemsDataError> {
    todo!()
}
