use std::collections::{HashMap, HashSet};

use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct CommandsData {
    pub cooldowns: HashMap<String, i32>,
    pub commands_which_spawn_mobs: HashSet<String>,
    pub commands_which_update_commands_leaderboard: HashSet<String>,
}
