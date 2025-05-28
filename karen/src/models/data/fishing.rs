use std::collections::HashMap;

use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub enum FishPeriodUnit {
    #[serde(rename = "day")]
    Day,
    #[serde(rename = "hour")]
    Hour,
}

#[derive(Debug, Deserialize)]
pub struct FishPricingPeriod {
    pub unit: FishPeriodUnit,
    pub period: i32,
    pub max: i32,
}

#[derive(Debug, Deserialize)]
pub struct FishPricing {
    pub base: i32,
    pub time_offset: i32,
    pub periods: Vec<FishPricingPeriod>,
}

#[derive(Debug, Deserialize)]
pub struct FishEntry {
    pub name: String,
    pub rarity: f32,
    pub pricing: FishPricing,
}

#[derive(Debug, Deserialize)]
pub struct FishingData {
    pub rarity_exponent: f32,
    pub fish: HashMap<String, FishEntry>,
}
