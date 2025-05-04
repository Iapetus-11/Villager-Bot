use thiserror::Error;

use crate::models::data::items::{ItemShopEntryBuyRequires, ItemsData};

#[derive(Debug, Error)]
pub enum ItemsDataError {
    #[error("The shop item {:#?} was not present in the item registry", .0)]
    ShopItemNotRegistered(String),

    #[error("The shop item {:#?}'s required item {:#?} was not present in the item registry", .0, .1)]
    ShopItemRequiredBuyItemNotRegistered(String, String),

    #[error("The findable item {:#?} was not present in the item registry", .0)]
    FindableItemNotRegistered(String),
}

pub fn check_items_data(data: &ItemsData) -> Result<(), ItemsDataError> {
    for (shop_item_name, shop_item_data) in data.shop.iter() {
        if !data.registry.contains_key(shop_item_name) {
            return Err(ItemsDataError::ShopItemNotRegistered(
                shop_item_name.clone(),
            ));
        }

        if let Some(ItemShopEntryBuyRequires {
            items: Some(items), ..
        }) = &shop_item_data.requires
        {
            for required_item_name in items.keys() {
                if !data.registry.contains_key(required_item_name) {
                    return Err(ItemsDataError::ShopItemRequiredBuyItemNotRegistered(
                        shop_item_name.clone(),
                        required_item_name.clone(),
                    ));
                }
            }
        }
    }

    for findable_item_name in data.findables.keys() {
        if !data.registry.contains_key(findable_item_name) {
            return Err(ItemsDataError::FindableItemNotRegistered(
                findable_item_name.clone(),
            ));
        }
    }

    Ok(())
}
