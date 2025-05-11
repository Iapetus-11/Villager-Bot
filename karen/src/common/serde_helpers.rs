use serde::{Deserialize, Deserializer};

/// Support the distinction between a missing field and a field with a value of null
pub fn deserialize_maybe_undefined<'de, T, D>(de: D) -> Result<Option<Option<T>>, D::Error>
where
    T: Deserialize<'de>,
    D: Deserializer<'de>,
{
    Deserialize::deserialize(de).map(Some)
}
