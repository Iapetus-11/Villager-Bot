use std::{error::Error as StdError, io::Cursor};

use image::{GenericImage, ImageReader, RgbaImage, imageops::FilterType};
use sqlx::PgConnection;

use crate::{common::xid::Xid, models::db::Badges};

pub async fn get_user_badges(
    db: &mut PgConnection,
    user_id: &Xid,
) -> Result<Option<Badges>, sqlx::Error> {
    sqlx::query_as!(
        Badges,
        r#"
            SELECT
                code_helper, translator, design_helper, bug_smasher, villager_og, supporter, uncle_scrooge, collector, beekeeper, pillager, murderer, enthusiast, fisherman
            FROM badges
            WHERE user_id = $1
        "#,
        user_id.as_bytes(),
    ).fetch_optional(&mut *db).await
}

// Port https://github.com/Iapetus-11/Villager-Bot/blob/8a36c4e565f4bf5ebcbd19689a3c7357c5f3805b/bot/cogs/core/badges.py#L18

fn get_badge_keys(badges: &Badges) -> Vec<String> {
    let mut badge_keys = Vec::<String>::new();

    macro_rules! push_bool_badge_key {
        ($key:ident) => {
            if (badges.$key) {
                badge_keys.push(stringify!($key).to_string());
            }
        };
    }

    macro_rules! push_i16_badge_key {
        ($key:ident) => {
            if (badges.$key > 0_i16) {
                badge_keys.push(format!("{}_{}", stringify!($key), badges.$key));
            }
        };
    }

    push_bool_badge_key!(code_helper);
    push_bool_badge_key!(translator);
    push_bool_badge_key!(design_helper);
    push_bool_badge_key!(bug_smasher);
    push_bool_badge_key!(villager_og);
    push_bool_badge_key!(supporter);
    push_bool_badge_key!(uncle_scrooge);
    push_i16_badge_key!(collector);
    push_i16_badge_key!(beekeeper);
    push_i16_badge_key!(pillager);
    push_i16_badge_key!(murderer);
    push_i16_badge_key!(enthusiast);
    push_i16_badge_key!(fisherman);

    badge_keys
}

pub async fn generate_user_badges_image(
    badges: &Badges,
) -> Result<Option<Vec<u8>>, Box<dyn StdError>> {
    let badge_keys = get_badge_keys(badges);

    if badge_keys.is_empty() {
        return Ok(None);
    }

    const BADGE_IMAGE_SIZE: u32 = 100;
    let total_image_width = (BADGE_IMAGE_SIZE * badge_keys.len() as u32).max(1000);

    let mut canvas_image = RgbaImage::new(total_image_width, BADGE_IMAGE_SIZE);

    for (idx, badge_key) in badge_keys.into_iter().enumerate() {
        let badge_image = ImageReader::open(format!("assets/badges/{badge_key}.png"))?
            .decode()?
            .resize(BADGE_IMAGE_SIZE, BADGE_IMAGE_SIZE, FilterType::Triangle);

        canvas_image.copy_from(&badge_image, idx as u32 * BADGE_IMAGE_SIZE, 0)?;
    }

    let mut image_bytes = Vec::<u8>::new();
    canvas_image.write_to(&mut Cursor::new(&mut image_bytes), image::ImageFormat::Png)?;

    Ok(Some(image_bytes))
}
