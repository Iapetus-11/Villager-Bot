use thiserror::Error;

use crate::models::data::items::ItemsData;

#[derive(Debug, Error)]
pub enum ItemsDataError {

}


pub fn check_items_data(data: &ItemsData) -> Result<(), ItemsDataError> {
    todo!()
}
