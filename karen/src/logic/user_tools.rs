use std::sync::LazyLock;

use sqlx::PgConnection;

use crate::{common::xid::Xid, logic::items::get_user_items};

use super::items::FilterItems;

static ALL_TOOLS: LazyLock<Vec<String>> = LazyLock::new(|| {
    [
        "Wood Pickaxe",
        "Stone Pickaxe",
        "Iron Pickaxe",
        "Gold Pickaxe",
        "Diamond Pickaxe",
        "Netherite Pickaxe",
        "Wood Sword",
        "Stone Sword",
        "Iron Sword",
        "Gold Sword",
        "Diamond Sword",
        "Netherite Sword",
        "Wood Hoe",
        "Stone Hoe",
        "Iron Hoe",
        "Gold Hoe",
        "Diamond Hoe",
        "Netherite Hoe",
    ]
    .map(String::from)
    .into_iter()
    .collect::<Vec<_>>()
});

#[derive(Debug, thiserror::Error)]
pub enum UserToolParseError {
    #[error("Item {:#?} is not a valid tool/item for this enum", .0)]
    InvalidItem(String),
}

#[derive(Debug, Clone, PartialEq, PartialOrd, Eq, Ord)]
#[repr(u8)]
pub enum UserPickaxe {
    Wood = 0,
    Stone = 1,
    Iron = 2,
    Gold = 3,
    Diamond = 4,
    Netherite = 5,
}

impl TryFrom<&str> for UserPickaxe {
    type Error = UserToolParseError;

    fn try_from(value: &str) -> Result<Self, Self::Error> {
        match value {
            "Wood Pickaxe" => Ok(Self::Wood),
            "Stone Pickaxe" => Ok(Self::Stone),
            "Iron Pickaxe" => Ok(Self::Iron),
            "Gold Pickaxe" => Ok(Self::Gold),
            "Diamond Pickaxe" => Ok(Self::Diamond),
            "Netherite Pickaxe" => Ok(Self::Netherite),
            other => Err(UserToolParseError::InvalidItem(other.to_string())),
        }
    }
}

impl ToString for UserPickaxe {
    fn to_string(&self) -> String {
        // TODO: Less clones
        ALL_TOOLS[self.clone() as usize].clone()
    }
}

#[derive(Debug, Clone, PartialEq, PartialOrd, Eq, Ord)]
#[repr(u8)]
pub enum UserSword {
    Wood = 0,
    Stone = 1,
    Iron = 2,
    Gold = 3,
    Diamond = 4,
    Netherite = 5,
}

impl TryFrom<&str> for UserSword {
    type Error = UserToolParseError;

    fn try_from(value: &str) -> Result<Self, Self::Error> {
        match value {
            "Wood Sword" => Ok(Self::Wood),
            "Stone Sword" => Ok(Self::Stone),
            "Iron Sword" => Ok(Self::Iron),
            "Gold Sword" => Ok(Self::Gold),
            "Diamond Sword" => Ok(Self::Diamond),
            "Netherite Sword" => Ok(Self::Netherite),
            other => Err(UserToolParseError::InvalidItem(other.to_string())),
        }
    }
}

impl ToString for UserSword {
    fn to_string(&self) -> String {
        // TODO: Less clones
        ALL_TOOLS[self.clone() as usize + 6].clone()
    }
}

#[derive(Debug, Clone, PartialEq, PartialOrd, Eq, Ord)]
#[repr(u8)]
pub enum UserHoe {
    Wood = 0,
    Stone = 1,
    Iron = 2,
    Gold = 3,
    Diamond = 4,
    Netherite = 5,
}

impl TryFrom<&str> for UserHoe {
    type Error = UserToolParseError;

    fn try_from(value: &str) -> Result<Self, Self::Error> {
        match value {
            "Wood Hoe" => Ok(Self::Wood),
            "Stone Hoe" => Ok(Self::Stone),
            "Iron Hoe" => Ok(Self::Iron),
            "Gold Hoe" => Ok(Self::Gold),
            "Diamond Hoe" => Ok(Self::Diamond),
            "Netherite Hoe" => Ok(Self::Netherite),
            other => Err(UserToolParseError::InvalidItem(other.to_string())),
        }
    }
}

impl ToString for UserHoe {
    fn to_string(&self) -> String {
        // TODO: Less clones
        ALL_TOOLS[self.clone() as usize + 12].clone()
    }
}

#[derive(Debug)]
pub struct UserTools {
    pub pickaxe: UserPickaxe,
    pub sword: UserSword,
    pub hoe: UserHoe,
}

// TODO: Optimize this to not fetch all tool items from DB (prob just move this logic to SQL?)

pub async fn get_user_tools(
    db: &mut PgConnection,
    user_id: &Xid,
) -> Result<UserTools, sqlx::Error> {
    let items = get_user_items(&mut *db, user_id, Some(FilterItems::Only(&ALL_TOOLS))).await?;

    let mut pickaxes = items
        .iter()
        .filter_map(|i| UserPickaxe::try_from(i.name.as_str()).ok())
        .collect::<Vec<_>>();
    pickaxes.sort();
    let pickaxe = pickaxes
        .into_iter()
        .next_back()
        .unwrap_or(UserPickaxe::Wood);

    let mut swords = items
        .iter()
        .filter_map(|i| UserSword::try_from(i.name.as_str()).ok())
        .collect::<Vec<_>>();
    swords.sort();
    let sword = swords.into_iter().next_back().unwrap_or(UserSword::Wood);

    let mut hoes = items
        .iter()
        .filter_map(|i| UserHoe::try_from(i.name.as_str()).ok())
        .collect::<Vec<_>>();
    hoes.sort();
    let hoe = hoes.into_iter().next_back().unwrap_or(UserHoe::Wood);

    Ok(UserTools {
        pickaxe,
        sword,
        hoe,
    })
}

#[cfg(test)]
mod tests {
    use crate::{
        common::testing::{CreateTestUser, PgPoolConn, create_test_user},
        logic::items::create_items,
        models::db::Item,
    };

    use super::*;

    #[sqlx::test]
    async fn test_get_user_tools(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        create_items(
            &mut db,
            &user.id,
            &[
                Item::from_registry("Iron Pickaxe", 1),
                Item::from_registry("Wood Pickaxe", 1),
                Item::from_registry("Netherite Sword", 1),
                Item::from_registry("Wood Sword", 1),
                Item::from_registry("Wood Hoe", 1),
                Item::from_registry("Stone Hoe", 1),
                Item::from_registry("Gold Hoe", 1),
            ],
        )
        .await
        .unwrap();

        let tools = get_user_tools(&mut db, &user.id).await.unwrap();

        assert_eq!(tools.pickaxe, UserPickaxe::Iron);
        assert_eq!(tools.sword, UserSword::Netherite);
        assert_eq!(tools.hoe, UserHoe::Gold);
    }

    #[sqlx::test]
    async fn test_get_user_tools_no_tools(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;

        let tools = get_user_tools(&mut db, &user.id).await.unwrap();

        assert_eq!(tools.pickaxe, UserPickaxe::Wood);
        assert_eq!(tools.sword, UserSword::Wood);
        assert_eq!(tools.hoe, UserHoe::Wood);
    }

    #[test]
    fn test_to_string_for_tool_enums() {
        assert_eq!(UserPickaxe::Wood.to_string(), "Wood Pickaxe");
        assert_eq!(UserPickaxe::Stone.to_string(), "Stone Pickaxe");
        assert_eq!(UserPickaxe::Iron.to_string(), "Iron Pickaxe");
        assert_eq!(UserPickaxe::Gold.to_string(), "Gold Pickaxe");
        assert_eq!(UserPickaxe::Diamond.to_string(), "Diamond Pickaxe");
        assert_eq!(UserPickaxe::Netherite.to_string(), "Netherite Pickaxe");

        assert_eq!(UserSword::Wood.to_string(), "Wood Sword");
        assert_eq!(UserSword::Stone.to_string(), "Stone Sword");
        assert_eq!(UserSword::Iron.to_string(), "Iron Sword");
        assert_eq!(UserSword::Gold.to_string(), "Gold Sword");
        assert_eq!(UserSword::Diamond.to_string(), "Diamond Sword");
        assert_eq!(UserSword::Netherite.to_string(), "Netherite Sword");

        assert_eq!(UserHoe::Wood.to_string(), "Wood Hoe");
        assert_eq!(UserHoe::Stone.to_string(), "Stone Hoe");
        assert_eq!(UserHoe::Iron.to_string(), "Iron Hoe");
        assert_eq!(UserHoe::Gold.to_string(), "Gold Hoe");
        assert_eq!(UserHoe::Diamond.to_string(), "Diamond Hoe");
        assert_eq!(UserHoe::Netherite.to_string(), "Netherite Hoe");
    }
}
