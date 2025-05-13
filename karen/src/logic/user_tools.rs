use std::sync::LazyLock;

use sqlx::PgConnection;

use crate::{common::xid::Xid, logic::items::get_user_items};

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

#[derive(Debug, PartialEq, PartialOrd, Eq, Ord)]
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

#[derive(Debug, PartialEq, PartialOrd, Eq, Ord)]
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

#[derive(Debug, PartialEq, PartialOrd, Eq, Ord)]
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
    let items = get_user_items(&mut *db, user_id, Some(&*ALL_TOOLS)).await?;

    let mut pickaxes = items
        .iter()
        .filter_map(|i| match UserPickaxe::try_from(i.name.as_str()) {
            Ok(up) => Some(up),
            _ => None,
        })
        .collect::<Vec<_>>();
    pickaxes.sort();
    let pickaxe = pickaxes.into_iter().last().unwrap_or(UserPickaxe::Wood);

    let mut swords = items
        .iter()
        .filter_map(|i| match UserSword::try_from(i.name.as_str()) {
            Ok(up) => Some(up),
            _ => None,
        })
        .collect::<Vec<_>>();
    swords.sort();
    let sword = swords.into_iter().last().unwrap_or(UserSword::Wood);

    let mut hoes = items
        .iter()
        .filter_map(|i| match UserHoe::try_from(i.name.as_str()) {
            Ok(up) => Some(up),
            _ => None,
        })
        .collect::<Vec<_>>();
    hoes.sort();
    let hoe = hoes.into_iter().last().unwrap_or(UserHoe::Wood);

    Ok(UserTools {
        pickaxe,
        sword,
        hoe,
    })
}

#[cfg(test)]
mod tests {
    use crate::{common::testing::{create_test_user, CreateTestUser, PgPoolConn}, logic::items::create_items, models::db::Item};

    use super::*;

    #[sqlx::test]
    async fn test_get_user_tools(mut db: PgPoolConn) {
        let user = create_test_user(&mut db, CreateTestUser::default()).await;
        
        create_items(&mut db, &user.id, &[
            Item::from_registry("Iron Pickaxe", 1),
            Item::from_registry("Wood Pickaxe", 1),
            Item::from_registry("Netherite Sword", 1),
            Item::from_registry("Wood Sword", 1),
            Item::from_registry("Wood Hoe", 1),
            Item::from_registry("Stone Hoe", 1),
            Item::from_registry("Gold Hoe", 1),
        ]).await.unwrap();

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
}
