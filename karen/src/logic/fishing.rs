use std::collections::HashMap;

use chrono::{Datelike, Timelike, Utc};
use sqlx::PgConnection;

use crate::common::data::FISHING_DATA;

pub fn get_current_fish_prices() -> HashMap<String, i64> {
    let duration_since_start_of_year = Utc::now() - Utc::now().with_month(1).unwrap().with_day(1).unwrap().with_minute(0).unwrap();

    let elapsed_weeks = duration_since_start_of_year.num_weeks();
    let elapsed_days = duration_since_start_of_year.num_days();
    let elapsed_hours = duration_since_start_of_year.num_hours();

    
}

pub async fn randomize_fish_prices(db: &mut PgConnection) -> Result<(), sqlx::Error> {
    for fish in FISHING_DATA.fish.values() {
        sqlx::query!(
            "UPDATE items SET sell_price = $2 WHERE name = $1",
            fish.name,
            fastrand::choice(fish.sell_price_range.0..fish.sell_price_range.1).unwrap()
        )
        .execute(&mut *db)
        .await?;
    }

    Ok(())
}
