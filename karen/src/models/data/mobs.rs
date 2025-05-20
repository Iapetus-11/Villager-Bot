use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct MobsData {
    pub spawn_rate_denominator: i16,
}
