use std::fmt::Debug;

use crate::common::data::ITEMS_DATA;

#[derive(Debug, thiserror::Error)]
pub enum ItemConstructionError {
    #[error("Item with key {:#?} is not present in item registry", .0)]
    NotRegistered(String),
}

#[derive(Debug)]
pub struct Item {
    pub name: String,
    pub sell_price: i32,
    pub amount: i64,
    pub sticky: bool,
    pub sellable: bool,
}

impl Item {
    pub fn try_from_registry(
        name: impl Into<String>,
        amount: i64,
    ) -> Result<Self, ItemConstructionError> {
        let name: String = name.into().to_lowercase();

        let Some(registry_data) = ITEMS_DATA.registry.get(&name) else {
            return Err(ItemConstructionError::NotRegistered(name));
        };

        Ok(Self {
            name: registry_data.name.clone(),
            sell_price: registry_data.sell_price,
            amount,
            sticky: registry_data.sticky,
            sellable: registry_data.sellable,
        })
    }

    pub fn from_registry(name: impl Into<String>, amount: i64) -> Self {
        Self::try_from_registry(name, amount).unwrap()
    }
}

#[cfg(test)]
mod tests {
    use crate::common::data::ITEMS_DATA;

    use super::*;

    #[test]
    fn test_try_from_registry() {
        let item_registry_entry = ITEMS_DATA
            .registry
            .get("komodo 30000 supernova aerial firework")
            .unwrap();

        let item = Item::try_from_registry("KOMODO 30000 SuperNova Aerial FIREworK", 2).unwrap();

        assert_eq!(item.name, "Komodo 30000 SuperNova Aerial Firework");
        assert_eq!(item.sell_price, item_registry_entry.sell_price);
        assert_eq!(item.amount, 2);
        assert_eq!(item.sticky, item_registry_entry.sticky);
        assert_eq!(item.sellable, item_registry_entry.sellable);
    }

    #[test]
    fn test_try_from_registry_unknown_item() {
        assert!(matches!(
            Item::try_from_registry("DNE", 69),
            Err(ItemConstructionError::NotRegistered(_))
        ));
    }
}
