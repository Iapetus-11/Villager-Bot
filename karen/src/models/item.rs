use std::fmt::Debug;

use serde::Serialize;
use sqlx::FromRow;

use crate::common::xid::Xid;

#[derive(Debug, FromRow, Serialize)]
pub struct Item {
    pub user_id: Xid,
    pub name: String,
    pub sell_price: i32,
    pub amount: i64,
    pub sticky: bool,
    pub sellable: bool,
}

impl Item {
    pub fn new(
        user_id: Xid,
        name: impl Into<String>,
        sell_price: i32,
        amount: i64,
        sticky: bool,
        sellable: bool,
    ) -> Self {
        Self {
            user_id,
            name: name.into(),
            sell_price,
            amount,
            sticky,
            sellable,
        }
    }
}
