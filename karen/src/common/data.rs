use crate::models::data::{commands::CommandsData, items::ItemsData, mobs::MobsData};
use std::{fs, sync::LazyLock};

pub static COMMANDS_DATA: LazyLock<CommandsData> = LazyLock::new(|| {
    let file_content = fs::read_to_string("data/commands.json").unwrap();
    serde_json::from_str(&file_content).unwrap()
});

pub static ITEMS_DATA: LazyLock<ItemsData> = LazyLock::new(|| {
    let file_content = fs::read_to_string("data/items.json").unwrap();
    serde_json::from_str(&file_content).unwrap()
});

pub static MOBS_DATA: LazyLock<MobsData> = LazyLock::new(|| {
    let file_content = fs::read_to_string("data/mobs.json").unwrap();
    serde_json::from_str(&file_content).unwrap()
});

#[cfg(test)]
mod tests {
    use crate::models::data::items::ItemShopEntryBuyRequires;

    use super::*;

    #[test]
    fn check_items_data() {
        for (shop_item_name, shop_item_data) in ITEMS_DATA.shop.iter() {
            if !ITEMS_DATA.registry.contains_key(shop_item_name) {
                panic!("Shop item not registered: {shop_item_name:#?}")
            }

            if let Some(ItemShopEntryBuyRequires {
                items: Some(items), ..
            }) = &shop_item_data.requires
            {
                for required_item_name in items.keys() {
                    if !ITEMS_DATA.registry.contains_key(required_item_name) {
                        panic!(
                            "Shop item {shop_item_name:#?} buy requirement {required_item_name:#?} is not registered"
                        );
                    }
                }
            }
        }

        for findable_item_name in ITEMS_DATA.findables.keys() {
            if !ITEMS_DATA.registry.contains_key(findable_item_name) {
                panic!("Findable item not registered: {findable_item_name:#?}");
            }
        }
    }
}
