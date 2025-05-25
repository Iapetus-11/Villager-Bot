use sqlx::PgConnection;

use crate::common::data::FISHING_DATA;

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
