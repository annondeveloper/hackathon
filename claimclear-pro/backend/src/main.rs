use axum::{routing::{delete, get, post}, Router};
use std::sync::Arc;
use tokio::sync::RwLock;
use tower_http::cors::{Any, CorsLayer};
use tower_http::trace::TraceLayer;

mod error;
mod handlers;
mod models;
mod openai;

use handlers::AppState;

#[tokio::main]
async fn main() {
    // Load .env file if present (silently ignore if missing).
    let _ = dotenvy::dotenv();

    // Initialise structured logging.
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "claimclear_backend=info,tower_http=info".into()),
        )
        .init();

    // Read API key from environment if available; otherwise start unconfigured.
    let api_key = std::env::var("OPENAI_API_KEY").ok();
    if api_key.is_some() {
        tracing::info!("OpenAI API key loaded from environment");
    } else {
        tracing::warn!(
            "OPENAI_API_KEY not set — configure it via the Settings UI or set the env var"
        );
    }

    let state = Arc::new(AppState {
        openai_api_key: RwLock::new(api_key),
        http_client: reqwest::Client::new(),
    });

    // CORS — allow the Vite dev server during development.
    let cors = CorsLayer::new()
        .allow_origin([
            "http://localhost:5173".parse().unwrap(),
            "http://127.0.0.1:5173".parse().unwrap(),
        ])
        .allow_methods(Any)
        .allow_headers(Any);

    let app = Router::new()
        .route("/api/explain", post(handlers::explain_claim))
        .route("/api/health", get(handlers::health_check))
        .route("/api/samples", get(handlers::get_samples))
        .route("/api/config", post(handlers::set_config))
        .route("/api/config", delete(handlers::delete_config))
        .route("/api/config/status", get(handlers::get_config_status))
        .layer(cors)
        .layer(TraceLayer::new_for_http())
        .with_state(state);

    let bind_addr = "0.0.0.0:3001";
    tracing::info!("ClaimClear AI Pro backend listening on {bind_addr}");

    let listener = tokio::net::TcpListener::bind(bind_addr)
        .await
        .expect("failed to bind to address");

    axum::serve(listener, app)
        .await
        .expect("server error");
}
