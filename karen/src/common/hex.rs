use std::num::ParseIntError;

pub fn decode_hex(str: &str) -> Result<Vec<u8>, ParseIntError> {
    (0..str.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&str[i..i + 2], 16))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_decode_hex() {
        for (hex, expected) in [
            ("c9490efbf8b45edbca5f2c70bc4ae2e2496fefd567da4e5bf64b0684dd3e1682", b"\xc9I\x0e\xfb\xf8\xb4^\xdb\xca_,p\xbcJ\xe2\xe2Io\xef\xd5g\xdaN[\xf6K\x06\x84\xdd>\x16\x82".to_vec()),
            ("EE", b"\xee".to_vec()),
        ] {
            assert_eq!(decode_hex(hex).unwrap(), expected);
        }
    }
}