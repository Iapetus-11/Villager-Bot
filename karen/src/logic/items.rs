use sqlx::PgConnection;

use crate::{common::xid::Xid, models::db::Item};

pub async fn create_items(
    db: &mut PgConnection,
    user_id: &Xid,
    items: &[Item],
) -> Result<(), sqlx::Error> {
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
        &items.iter().map(|_| user_id.as_bytes().to_vec()).collect::<Vec<_>>()[..],
        &items.iter().map(|i| i.name.clone()).collect::<Vec<_>>()[..],
        &items.iter().map(|i| i.sell_price).collect::<Vec<_>>()[..],
        &items.iter().map(|i| i.amount).collect::<Vec<_>>()[..],
        &items.iter().map(|i| i.sticky).collect::<Vec<_>>()[..],
        &items.iter().map(|i| i.sellable).collect::<Vec<_>>()[..],
    ).execute(&mut *db).await?;

    Ok(())
}

pub async fn get_user_items(
    db: &mut PgConnection,
    user_id: &Xid,
    filter_items: Option<&[String]>,
) -> Result<Vec<Item>, sqlx::Error> {
    match filter_items {
        Some(filter_items) => {
            sqlx::query_as!(
                Item,
                r#"
                    SELECT name, sell_price, amount, sticky, sellable
                    FROM items
                    WHERE user_id = $1 AND name = ANY($2::VARCHAR[])
                "#,
                user_id.as_bytes(),
                filter_items,
            )
            .fetch_all(&mut *db)
            .await
        }
        None => {
            sqlx::query_as!(
                Item,
                r#"
                    SELECT name, sell_price, amount, sticky, sellable
                    FROM items
                    WHERE user_id = $1
                "#,
                user_id.as_bytes(),
            )
            .fetch_all(&mut *db)
            .await
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    use crate::common::{
        data::ITEMS_DATA,
        testing::{CreateTestUser, PgPoolConn, create_test_user},
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

        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        create_items(
            &mut db,
            &user.id,
            &[
                Item::from_registry("Slime Ball", 7),
                Item::from_registry("Diamond Pickaxe", 1),
                Item::from_registry("jar of bees", 420),
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
            &user.id,
            &[
                Item::from_registry("slime BALL", 2),
                Item::from_registry("jar OF BEES", 246),
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

    #[sqlx::test]
    async fn test_get_items(mut db: PgPoolConn) {
        let user_1 = create_test_user(&mut db, CreateTestUser::default()).await;
        let user_2 = create_test_user(
            &mut db,
            CreateTestUser {
                discord_id: None,
                ..CreateTestUser::default()
            },
        )
        .await;

        create_items(
            &mut db,
            &user_1.id,
            &[
                Item::from_registry("Wood Pickaxe", 1),
                Item::from_registry("Diamond Pickaxe", 1),
                Item::from_registry("Diamond Sword", 1),
            ],
        )
        .await
        .unwrap();

        create_items(
            &mut db,
            &user_2.id,
            &[
                Item::from_registry("Netherite Pickaxe", 1),
                Item::from_registry("Netherite Sword", 1),
            ],
        )
        .await
        .unwrap();

        let user_1_items = get_user_items(&mut db, &user_1.id, None).await.unwrap();
        assert_eq!(user_1_items.len(), 3);
        assert!(user_1_items.iter().any(|i| i.name == "Wood Pickaxe"));
        assert!(user_1_items.iter().any(|i| i.name == "Diamond Pickaxe"));
        assert!(user_1_items.iter().any(|i| i.name == "Diamond Sword"));

        let user_2_items = get_user_items(&mut db, &user_2.id, None).await.unwrap();
        assert_eq!(user_2_items.len(), 2);
        assert!(user_2_items.iter().any(|i| i.name == "Netherite Pickaxe"));
        assert!(user_2_items.iter().any(|i| i.name == "Netherite Sword"));

        let user_1_pickaxes = get_user_items(
            &mut db,
            &user_1.id,
            Some(&[
                "Wood Pickaxe".into(),
                "Diamond Pickaxe".into(),
                "Netherite Pickaxe".into(),
            ]),
        )
        .await
        .unwrap();
        assert_eq!(user_1_pickaxes.len(), 2);
        assert!(user_1_pickaxes.iter().any(|i| i.name == "Wood Pickaxe"));
        assert!(user_1_pickaxes.iter().any(|i| i.name == "Diamond Pickaxe"));

        let user_2_pickaxes = get_user_items(
            &mut db,
            &user_2.id,
            Some(&[
                "Wood Pickaxe".into(),
                "Diamond Pickaxe".into(),
                "Netherite Pickaxe".into(),
            ]),
        )
        .await
        .unwrap();
        assert_eq!(user_2_pickaxes.len(), 1);
        assert!(
            user_2_pickaxes
                .iter()
                .any(|i| i.name == "Netherite Pickaxe")
        );
    }
}
