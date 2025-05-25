use crate::models::data::{
    commands::CommandsData, fishing::FishingData, items::ItemsData, mobs::MobsData,
};
use std::{fs, sync::LazyLock};

macro_rules! lazylock_with_json_data {
    ($file:literal) => {
        LazyLock::new(|| {
            let file_content = fs::read_to_string(format!("data/{}.json", $file)).unwrap();
            serde_json::from_str(&file_content).unwrap()
        })
    };
}

pub static COMMANDS_DATA: LazyLock<CommandsData> = lazylock_with_json_data!("commands");
pub static ITEMS_DATA: LazyLock<ItemsData> = lazylock_with_json_data!("items");
pub static MOBS_DATA: LazyLock<MobsData> = lazylock_with_json_data!("mobs");
pub static FISHING_DATA: LazyLock<FishingData> = lazylock_with_json_data!("fishing");

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

        for fish in FISHING_DATA.fish.values() {
            if !ITEMS_DATA.registry.contains_key(&fish.name.to_lowercase()) {
                panic!("Fish is not registered: {}", fish.name);
            }
        }
    }
}
