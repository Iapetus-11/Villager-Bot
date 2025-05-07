use crate::models::data::{commands::CommandsData, items::ItemsData};
use std::{error::Error as StdError, fs, sync::LazyLock};

pub fn load_commands_data() -> Result<CommandsData, Box<dyn StdError>> {
    let file_content = fs::read_to_string("data/commands.json")?;
    Ok(serde_json::from_str(&file_content)?)
}

pub fn load_items_data() -> Result<ItemsData, Box<dyn StdError>> {
    let file_content = fs::read_to_string("data/items.json")?;
    Ok(serde_json::from_str(&file_content)?)
}

pub static COMMANDS_DATA: LazyLock<CommandsData> = LazyLock::new(|| load_commands_data().unwrap());

pub static ITEMS_DATA: LazyLock<ItemsData> = LazyLock::new(|| load_items_data().unwrap());
