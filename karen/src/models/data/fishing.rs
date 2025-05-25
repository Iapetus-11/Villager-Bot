use std::collections::HashMap;

use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct FishEntry {
    pub name: String,
    pub sell_price_range: (i32, i32),
    pub rarity: f32,
}

#[derive(Debug, Deserialize)]
pub struct FishingData {
    pub rarity_exponent: f32,
    pub fish: HashMap<String, FishEntry>,
}
