use std::{
    collections::{BTreeMap, BTreeSet},
    error::Error as StdError,
    fs,
};

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

#[derive(Debug, Deserialize)]
pub struct ItemsData {
    pub registry: BTreeMap<String, ItemRecord>,
    pub shop: BTreeMap<String, ItemShopEntry>,
    pub findables: BTreeMap<String, ItemFindableEntry>,
}

pub fn load() -> Result<ItemsData, Box<dyn StdError>> {
    let file_content = fs::read_to_string("data/items.json")?;
    Ok(serde_json::from_str(&file_content)?)
}
