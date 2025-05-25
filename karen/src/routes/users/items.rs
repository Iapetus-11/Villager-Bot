use poem::{
    handler,
    web::{Data, Json, Path, Query},
};
use serde::{Deserialize, Serialize};

use crate::{
    common::{data::ITEMS_DATA, security::RequireAuthedClient, xid::Xid},
    logic::items::{FilterItems, get_user_items},
    models::db::Item,
};

#[derive(Serialize)]
#[cfg_attr(test, derive(Deserialize))]
struct ItemView {
    name: String,
    sell_price: i32,
    amount: i64,
    sticky: bool,
    sellable: bool,
}

#[derive(Deserialize)]
#[cfg_attr(test, derive(Serialize))]
struct ListQueryParams {
    #[serde(default)]
    category: Option<String>,
}

#[handler]
pub async fn list(
    db: Data<&sqlx::PgPool>,
    Path((user_id,)): Path<(Xid,)>,
    query_params: Query<ListQueryParams>,
    _: RequireAuthedClient,
) -> Result<Json<Vec<ItemView>>, poem::Error> {
    let mut db = db.acquire().await.unwrap();

    let mut filter_items = Vec::<String>::new();
    let filter_items: Option<FilterItems<'_>> = match &query_params.category {
        None => None,
        Some(category) if category == "misc" => {
            // for item in ITEMS_DATA.registry.values()
            todo!();
        }
        Some(category) => {
            for item in ITEMS_DATA.registry.values() {
                if item.categories.iter().any(|ic| ic == category) {
                    filter_items.push(item.name.clone());
                }
            }

            Some(FilterItems::Only(filter_items.as_slice()))
        }
    };

    let items = get_user_items(&mut db, &user_id, filter_items)
        .await
        .unwrap();

    Ok(Json(
        items
            .into_iter()
            .map(
                |Item {
                     name,
                     sell_price,
                     amount,
                     sticky,
                     sellable,
                 }| {
                    ItemView {
                        name,
                        sell_price,
                        amount,
                        sticky,
                        sellable,
                    }
                },
            )
            .collect(),
    ))
}
