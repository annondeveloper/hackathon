use axum::{routing::{get, post}, Router};
use std::sync::Arc;
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

    // Read required configuration from the environment.
    let api_key = std::env::var("OPENAI_API_KEY").expect(
        "OPENAI_API_KEY must be set. Create a .env file or export the variable.",
    );

    let state = Arc::new(AppState {
        openai_api_key: api_key,
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
