use actix_multipart::Multipart;
use actix_web::{web, App, HttpResponse, HttpServer, Responder};
use bytes::BytesMut;
use futures_util::TryStreamExt as _;
use image::{imageops::FilterType, DynamicImage, ImageFormat, GenericImageView};
use serde::Serialize;
use std::io::Cursor;
use tracing::{error, info};

#[derive(Serialize)]
struct ErrorResponse<'a> {
    success: bool,
    message: &'a str,
}

async fn health() -> impl Responder {
    HttpResponse::Ok().json(serde_json::json!({"success": true, "service": "rust-images"}))
}

async fn sanitize(mut payload: Multipart) -> actix_web::Result<HttpResponse> {
    let mut data = BytesMut::new();

    while let Ok(Some(mut field)) = payload.try_next().await {
        let cd = field.content_disposition();
        let name = cd.get_name().unwrap_or("").to_string();
        if name != "file" { continue; }
        while let Some(chunk) = field.try_next().await? {
            if data.len() + chunk.len() > 6 * 1024 * 1024 { // 6MB guard
                return Ok(HttpResponse::BadRequest().json(ErrorResponse{ success: false, message: "Arquivo muito grande" }));
            }
            data.extend_from_slice(&chunk);
        }
    }

    if data.is_empty() {
        return Ok(HttpResponse::BadRequest().json(ErrorResponse{ success: false, message: "Arquivo ausente" }));
    }

    // Keep a reader if needed for future extensions; silence unused warning
    let _reader = Cursor::new(&data);
    let img = match image::load_from_memory(&data) {
        Ok(i) => i,
        Err(e) => {
            error!(?e, "falha ao decodificar imagem");
            return Ok(HttpResponse::BadRequest().json(ErrorResponse{ success: false, message: "Imagem inválida" }));
        }
    };

    let (w, h) = img.dimensions();
    if w as u64 * h as u64 > 30_000_000 { // 30MP cap
        return Ok(HttpResponse::BadRequest().json(ErrorResponse{ success: false, message: "Imagem muito grande" }));
    }

    let resized: DynamicImage = img.resize(256, 256, FilterType::Lanczos3);

    // Prefer WEBP output, fallback to PNG (use separate buffers to avoid E0499)
    let (out, content_type) = {
        let mut out_webp: Vec<u8> = Vec::new();
        match resized.write_to(&mut Cursor::new(&mut out_webp), ImageFormat::WebP) {
            Ok(_) => (out_webp, "image/webp"),
            Err(e) => {
                error!(?e, "erro ao escrever webp; tentando png");
                let mut out_png: Vec<u8> = Vec::new();
                if let Err(e2) = resized.write_to(&mut Cursor::new(&mut out_png), ImageFormat::Png) {
                    error!(?e2, "erro ao escrever png");
                    return Ok(HttpResponse::InternalServerError()
                        .json(ErrorResponse{ success: false, message: "Falha no processamento" }));
                }
                (out_png, "image/png")
            }
        }
    };

    Ok(HttpResponse::Ok().content_type(content_type).body(out))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter("info")
        .init();

    let addr_raw = std::env::var("RUST_IMAGES_ADDR").unwrap_or_else(|_| "127.0.0.1:8081".to_string());
    let addr_trim = addr_raw.trim();
    // Parse "host:port" robustly and fallback to defaults if needed
    let (host, port): (String, u16) = match addr_trim.rsplit_once(':') {
        Some((h, p_str)) => match p_str.trim().parse::<u16>() {
            Ok(p) if p > 0 => (h.trim().to_string(), p),
            _ => ("127.0.0.1".to_string(), 8081),
        },
        None => (addr_trim.to_string(), 8081),
    };
    info!(host=%host, port=%port, "rust image service starting");

    HttpServer::new(|| {
        App::new()
            .route("/health", web::get().to(health))
            .route("/sanitize", web::post().to(sanitize))
    })
    .bind((host, port))?
    .run()
    .await
}
