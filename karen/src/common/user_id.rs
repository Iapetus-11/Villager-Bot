use std::fmt;

use serde::{
    Deserialize, Deserializer, Serialize,
    de::{self, Visitor},
};

use crate::common::xid::Xid;

#[derive(Debug, PartialEq, Eq)]
pub enum UserId {
    Xid(Xid),
    Discord(i64),
}

impl UserId {
    #[allow(clippy::inherent_to_string)]
    pub fn to_string(&self) -> String {
        match self {
            UserId::Xid(xid) => xid.to_string(),
            UserId::Discord(snowflake) => snowflake.to_string(),
        }
    }
}

// -------------------------------------------------------------------------------------------------
// Serde

impl Serialize for UserId {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        match self {
            UserId::Xid(xid) => serializer.serialize_str(&xid.to_string()),
            UserId::Discord(discord_id) => serializer.serialize_i64(*discord_id),
        }
    }
}

struct UserIdVisitor;

impl<'de> Visitor<'de> for UserIdVisitor {
    type Value = UserId;

    fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
        formatter.write_str("A user's Discord ID (i64) or a string representation of an Xid")
    }

    fn visit_i64<E>(self, v: i64) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        Ok(UserId::Discord(v))
    }

    fn visit_u64<E>(self, v: u64) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        Ok(UserId::Discord(v as i64))
    }

    fn visit_str<E>(self, v: &str) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        match Xid::try_from(v) {
            Ok(xid) => Ok(UserId::Xid(xid)),
            Err(_) => match v.parse::<u64>() {
                Ok(discord_id) => Ok(UserId::Discord(discord_id as i64)),
                Err(_) => Err(E::custom(
                    "Expected valid XID string representation or a Discord snowflake",
                )),
            },
        }
    }

    fn visit_string<E>(self, v: String) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        self.visit_str(&v)
    }

    fn visit_borrowed_str<E>(self, v: &'de str) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        self.visit_str(v)
    }
}

impl<'de> Deserialize<'de> for UserId {
    fn deserialize<D>(deserializer: D) -> Result<UserId, D::Error>
    where
        D: Deserializer<'de>,
    {
        deserializer.deserialize_str(UserIdVisitor)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_serialize_user_id_xid() {
        let user_id_xid = Xid::new();
        let user_id = UserId::Xid(user_id_xid);

        assert_eq!(
            serde_json::to_string(&user_id).unwrap(),
            serde_json::to_string(&user_id_xid.to_string()).unwrap()
        );
    }

    #[test]
    fn test_serialize_user_id_discord() {
        let user_id_discord = 536986067140608041_i64;
        let user_id = UserId::Discord(user_id_discord);

        assert_eq!(
            serde_json::to_string(&user_id).unwrap(),
            user_id_discord.to_string()
        );
    }

    #[test]
    fn test_deserialize_user_id_xid() {
        let user_id = UserId::Xid(Xid::new());
        let serialized_user_id = serde_json::to_string(&user_id).unwrap();

        let mut deserializer = serde_json::Deserializer::from_str(&serialized_user_id);

        assert_eq!(UserId::deserialize(&mut deserializer).unwrap(), user_id);
    }

    #[test]
    fn test_deserialize_user_id_discord() {
        let user_id = UserId::Discord(536986067140608041);
        let serialized_user_id = serde_json::to_string(&user_id.to_string()).unwrap();

        let mut deserializer = serde_json::Deserializer::from_str(&serialized_user_id);

        assert_eq!(UserId::deserialize(&mut deserializer).unwrap(), user_id);
    }
}
