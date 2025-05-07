use std::collections::{BTreeMap, BTreeSet};

use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct ItemRecord {
    pub name: String,
    pub sell_price: i32,
    pub sticky: bool,
    pub sellable: bool,
}

#[derive(Debug, Deserialize)]
pub struct ItemShopEntryBuyRequires {
    pub count_lt: Option<i64>,
    pub items: Option<BTreeMap<String, i64>>,
}

#[derive(Debug, Deserialize)]
pub struct ItemShopEntry {
    pub categories: Vec<String>,
    pub buy_price: i32,
    pub requires: Option<ItemShopEntryBuyRequires>,
}

#[derive(Debug, Deserialize)]
pub struct ItemFindableEntry {
    pub rarity: i32,
    pub tags: BTreeSet<String>,
}

pub type ItemRegistry = BTreeMap<String, ItemRecord>;
pub type ItemShopData = BTreeMap<String, ItemShopEntry>;
pub type ItemFindableData = BTreeMap<String, ItemFindableEntry>;

#[derive(Debug, Deserialize)]
pub struct ItemsData {
    pub registry: ItemRegistry,
    pub shop: ItemShopData,
    pub findables: ItemFindableData,
}
