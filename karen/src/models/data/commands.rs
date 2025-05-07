use std::collections::BTreeMap;

use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct CommandsData {
    pub cooldowns: BTreeMap<String, i32>,
}
