use std::collections::BTreeMap;
use std::error::Error as StdError;
use std::fs;

use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct CommandsData {
    pub cooldowns: BTreeMap<String, i32>,
}

pub fn load() -> Result<CommandsData, Box<dyn StdError>> {
    let file_content = fs::read_to_string("data/commands.json")?;
    Ok(serde_json::from_str(&file_content)?)
}
