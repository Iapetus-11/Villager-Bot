use std::{fmt, str::FromStr};

use serde::{
    Deserialize, Deserializer, Serialize,
    de::{self, Visitor},
};
use thiserror::Error;

use super::hex::decode_hex;

/// Wrapper around xid::Id to add compatibility with Serde and Sqlx
#[derive(Debug, Copy, Clone, PartialEq, Eq)]
pub struct Xid(xid::Id);

/// Extension of xid::ParseIdError
#[allow(clippy::enum_variant_names)]
#[derive(Error, Debug)]
pub enum XidParseError {
    /// Returned when the id had length other than 20.
    #[error("invalid length {}", .0)]
    InvalidLength(usize),
    /// Returned when the id had character not in `[0-9a-v]`.
    #[error("invalid character '{}'", .0)]
    InvalidCharacter(char),
    /// Returned in some cases when failing to parse an Xid from a hex string
    #[error("invalid hex string")]
    InvalidHexString,
}

impl From<xid::ParseIdError> for XidParseError {
    fn from(value: xid::ParseIdError) -> Self {
        match value {
            xid::ParseIdError::InvalidCharacter(c) => XidParseError::InvalidCharacter(c),
            xid::ParseIdError::InvalidLength(l) => XidParseError::InvalidLength(l),
        }
    }
}

impl std::ops::Deref for Xid {
    type Target = xid::Id;

    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

impl std::ops::DerefMut for Xid {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.0
    }
}

impl Xid {
    pub fn new() -> Xid {
        Xid(xid::new())
    }
}

impl From<Vec<u8>> for Xid {
    fn from(value: Vec<u8>) -> Self {
        let mut id_bytes = [0_u8; 12];
        id_bytes.clone_from_slice(&value);

        Xid(xid::Id(id_bytes))
    }
}

impl TryFrom<&str> for Xid {
    type Error = XidParseError;

    fn try_from(value: &str) -> Result<Self, Self::Error> {
        if value.len() == 24 {
            return Ok(Self::from(
                decode_hex(value).map_err(|_| XidParseError::InvalidHexString)?,
            ));
        }

        xid::Id::from_str(value)
            .map_err(XidParseError::from)
            .map(Xid)
    }
}

// -------------------------------------------------------------------------------------------------
// Serde

impl Serialize for Xid {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        serializer.serialize_str(&self.to_string())
    }
}

struct XidVisitor;

impl<'de> Visitor<'de> for XidVisitor {
    type Value = Xid;

    fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
        formatter.write_str("A valid string representation of an XID")
    }

    fn visit_str<E>(self, v: &str) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        Xid::try_from(v).map_err(|_| E::custom("Expected valid XID string representation"))
    }

    fn visit_string<E>(self, v: String) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        Xid::try_from(v.as_str()).map_err(|_| E::custom("Expected valid XID string representation"))
    }

    fn visit_borrowed_str<E>(self, v: &'de str) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        Xid::try_from(v).map_err(|_| E::custom("Expected valid XID string representation"))
    }
}

impl<'de> Deserialize<'de> for Xid {
    fn deserialize<D>(deserializer: D) -> Result<Xid, D::Error>
    where
        D: Deserializer<'de>,
    {
        deserializer.deserialize_str(XidVisitor)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_xid_to_from_string() {
        let xid = Xid::new();
        let str_xid = xid.to_string();

        assert_eq!(str_xid.len(), 20);
        assert_eq!(xid, Xid::try_from(str_xid.as_str()).unwrap());
    }

    #[test]
    fn test_serialize_xid() {
        let xid = Xid::new();
        let serialized_xid = serde_json::to_string(&xid).unwrap();

        assert_eq!(serialized_xid, serde_json::to_string(&xid.to_string()).unwrap())
    }

    #[test]
    fn test_deserialize_xid() {
        let xid = Xid::new();
        let serialized_xid = serde_json::to_string(&xid.to_string()).unwrap();

        let mut deserializer = serde_json::Deserializer::from_str(&serialized_xid);

        assert_eq!(Xid::deserialize(&mut deserializer).unwrap(), xid);
    }
}