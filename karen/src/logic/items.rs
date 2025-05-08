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
            ON CONFLICT (user_id, name) DO UPDATE SET
                amount = items.amount + EXCLUDED.amount;
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

#[cfg(test)]
mod tests {
    use super::*;

    use crate::common::{
        data::ITEMS_DATA,
        testing::{PgPoolConn, create_test_user},
    };

    #[sqlx::test]
    fn test_create_items(mut db: PgPoolConn) {
        async fn assert_item_record_correct(
            db: &mut PgConnection,
            item: &str,
            expected_amount: i64,
        ) {
            let registry_entry = ITEMS_DATA.registry.get(&item.to_ascii_lowercase()).unwrap();
            let item = sqlx::query!("SELECT * FROM items WHERE name = $1", item)
                .fetch_one(&mut *db)
                .await
                .unwrap();

            assert_eq!(item.sell_price, registry_entry.sell_price);
            assert_eq!(item.amount, expected_amount);
            assert_eq!(item.sticky, registry_entry.sticky);
            assert_eq!(item.sellable, registry_entry.sellable);
        }

        let user = create_test_user(&mut db).await;

        create_items(
            &mut db,
            &[
                Item::from_registry(user.id, "Slime Ball", 7),
                Item::from_registry(user.id, "Diamond Pickaxe", 1),
                Item::from_registry(user.id, "jar of bees", 420),
            ],
        )
        .await
        .unwrap();

        for (item, expected_amount) in [
            ("Slime Ball", 7),
            ("Diamond Pickaxe", 1),
            ("Jar Of Bees", 420),
        ] {
            assert_item_record_correct(&mut db, item, expected_amount).await;
        }

        create_items(
            &mut db,
            &[
                Item::from_registry(user.id, "slime BALL", 2),
                Item::from_registry(user.id, "jar OF BEES", 246),
            ],
        )
        .await
        .unwrap();

        for (item, expected_amount) in [
            ("Slime Ball", 9),
            ("Diamond Pickaxe", 1),
            ("Jar Of Bees", 666),
        ] {
            assert_item_record_correct(&mut db, item, expected_amount).await;
        }
    }
}
