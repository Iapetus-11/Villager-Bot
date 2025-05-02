use std::{any::type_name, env, str::FromStr};

pub struct Config {
    pub database_url: String,
    pub database_pool_size: u32,
    pub server_host_address: String,
    pub auth_token: String,
}

fn get_env<T: FromStr>(key: &str) -> T {
    let string = env::var(key).unwrap_or_else(|_| panic!("Please set {key} in your .env"));

    let parsed = string.parse::<T>();

    match parsed {
        Ok(value) => value,
        Err(_) => {
            let type_name = type_name::<T>();
            panic!("Expected {key} to be a valid {type_name} in your .env");
        }
    }
}

pub fn load() -> Config {
    dotenv::dotenv().unwrap();

    let database_url: String = get_env("DATABASE_URL");
    let database_pool_size: u32 = get_env("DATABASE_POOL_SIZE");
    let server_host_address: String = get_env("SERVER_HOST_ADDRESS");
    let auth_token: String = get_env("AUTH_TOKEN");

    Config {
        database_url,
        database_pool_size,
        server_host_address,
        auth_token,
    }
}
