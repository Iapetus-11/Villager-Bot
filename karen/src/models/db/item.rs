use std::fmt::Debug;

use serde::Serialize;
use sqlx::FromRow;

use crate::common::{data::ITEMS_DATA, xid::Xid};

#[derive(Debug, thiserror::Error)]
pub enum ItemConstructionError {
    #[error("Item with key {:#?} is not present in item registry", .0)]
    NotRegistered(String),
}

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
    pub fn try_from_registry(
        user_id: Xid,
        name: impl Into<String>,
        amount: i64,
    ) -> Result<Self, ItemConstructionError> {
        let name: String = name.into().to_lowercase();

        let Some(registry_data) = ITEMS_DATA.registry.get(&name) else {
            return Err(ItemConstructionError::NotRegistered(name));
        };

        Ok(Self {
            user_id,
            name: registry_data.name.clone(),
            sell_price: registry_data.sell_price,
            amount,
            sticky: registry_data.sticky,
            sellable: registry_data.sellable,
        })
    }

    pub fn from_registry(user_id: Xid, name: impl Into<String>, amount: i64) -> Self {
        Self::try_from_registry(user_id, name, amount).unwrap()
    }
}

#[cfg(test)]
mod tests {
    #[test]
    fn test_try_from_registry() {
        todo!();
    }
}
