use std::collections::HashMap;

use chrono::{Datelike, Timelike, Utc};
use sqlx::PgConnection;

use crate::{common::data::FISHING_DATA, models::data::fishing::FishPeriodUnit};

pub fn get_current_fish_prices() -> HashMap<String, i32> {
    let mut fish_pricing = HashMap::with_capacity(7);

    let duration_since_start_of_year = Utc::now()
        - Utc::now()
            .with_month(1)
            .unwrap()
            .with_day(1)
            .unwrap()
            .with_minute(0)
            .unwrap();

    let days = duration_since_start_of_year.num_days();
    let hours = duration_since_start_of_year.num_hours();

    for fish in FISHING_DATA.fish.values() {
        let mut fish_price = fish.pricing.base;

        for period in fish.pricing.periods.iter() {
            let period_value = match period.unit {
                FishPeriodUnit::Day => days,
                FishPeriodUnit::Hour => hours,
            } as i32;
            let period_value = ((period_value + fish.pricing.time_offset) % period.period) + 1;

            let rate = period_value as f32 / period.period as f32;
            let period_price = (rate * period.max as f32) as i32;

            fish_price += period_price;
        }

        fish_pricing.insert(fish.name.clone(), fish_price);
    }

    fish_pricing
}

pub async fn update_fishing_prices(db: &mut PgConnection) -> Result<(), sqlx::Error> {
    let fish_pricing = get_current_fish_prices();

    for fish in FISHING_DATA.fish.values() {
        sqlx::query!(
            "UPDATE items SET sell_price = $2 WHERE name = $1",
            fish.name,
            fish_pricing[&fish.name],
        )
        .execute(&mut *db)
        .await?;
    }

    Ok(())
}
