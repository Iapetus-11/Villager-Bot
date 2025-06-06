use std::collections::HashMap;

use poem::{
    handler,
    web::{Json, Path},
};
use serde::Serialize;

use crate::{common::data::ITEMS_DATA, models::data::items::ItemShopEntry};

#[derive(Serialize)]
#[cfg_attr(test, derive(serde::Deserialize))]
struct ShopItemEntryBuyRequiresView {
    count_lt: Option<i64>,
    items: Option<HashMap<String, i64>>,
}

#[derive(Serialize)]
#[cfg_attr(test, derive(serde::Deserialize))]
struct ShopItemView {
    name: String,
    buy_price: i32,
    requires: Option<ShopItemEntryBuyRequiresView>,
}

impl From<(&String, &ItemShopEntry)> for ShopItemView {
    fn from((key, value): (&String, &ItemShopEntry)) -> Self {
        Self {
            name: ITEMS_DATA.registry[key].name.clone(),
            buy_price: value.buy_price,
            requires: value
                .requires
                .as_ref()
                .map(|req| ShopItemEntryBuyRequiresView {
                    count_lt: req.count_lt,
                    items: req.items.clone(),
                }),
        }
    }
}

#[handler]
pub async fn items_for_category(
    Path((category,)): Path<(String,)>,
) -> Json<HashMap<String, ShopItemView>> {
    Json(HashMap::from_iter(
        ITEMS_DATA
            .shop
            .iter()
            .filter(|(_, i)| i.categories.contains(&category))
            .map(|(k, e)| (k.clone(), ShopItemView::from((k, e)))),
    ))
}
