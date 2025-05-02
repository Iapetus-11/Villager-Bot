use sqlx::PgConnection;

use crate::models::db::Item;

pub async fn create_items(db: &mut PgConnection, items: &[Item]) -> Result<(), sqlx::Error> {
    sqlx::query!(
        r#"
            INSERT INTO items
                (user_id, name, sell_price, amount, sticky, sellable)
            SELECT * FROM UNNEST(
                $1::BYTEA[], $2::VARCHAR[], $3::INTEGER[], $4::BIGINT[], $5::BOOLEAN[], $6::BOOLEAN[]
            )
        "#,
        &items.iter().map(|i| i.user_id.as_bytes().to_vec()).collect::<Vec<_>>()[..],
        &items.iter().map(|i| i.name.clone()).collect::<Vec<_>>()[..],
        &items.iter().map(|i| i.sell_price).collect::<Vec<_>>()[..],
        &items.iter().map(|i| i.amount).collect::<Vec<_>>()[..],
        &items.iter().map(|i| i.sticky).collect::<Vec<_>>()[..],
        &items.iter().map(|i| i.sellable).collect::<Vec<_>>()[..],
    ).execute(&mut *db).await?;

    Ok(())
}
