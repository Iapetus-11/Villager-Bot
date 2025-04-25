use std::fmt;

use serde::{de::{self, Visitor}, Deserialize, Deserializer, Serialize};

use super::xid::Xid;

pub enum UserId {
    Xid(Xid),
    Discord(i64),
}

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
        Xid::try_from(v).map(|xid| UserId::Xid(xid)).map_err(|_| E::custom("Expected valid XID string representation"))
    }

    fn visit_string<E>(self, v: String) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        Xid::try_from(v.as_str()).map(|xid| UserId::Xid(xid)).map_err(|_| E::custom("Expected valid XID string representation"))
    }

    fn visit_borrowed_str<E>(self, v: &'de str) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        Xid::try_from(v).map(|xid| UserId::Xid(xid)).map_err(|_| E::custom("Expected valid XID string representation"))
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
