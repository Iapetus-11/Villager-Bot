use std::num::ParseIntError;

pub fn decode_hex(str: &str) -> Result<Vec<u8>, ParseIntError> {
    (0..str.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&str[i..i + 2], 16))
        .collect()
}
