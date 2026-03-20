use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde_json::json;
use std::fmt;

/// Application-wide error type that converts into an Axum response.
#[derive(Debug)]
pub enum AppError {
    /// Errors originating from the OpenAI API call.
    OpenAi(String),
    /// Request validation failures.
    Validation(String),
    /// Catch-all for unexpected internal errors.
    Internal(String),
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AppError::OpenAi(msg) => write!(f, "OpenAI error: {msg}"),
            AppError::Validation(msg) => write!(f, "Validation error: {msg}"),
            AppError::Internal(msg) => write!(f, "Internal error: {msg}"),
        }
    }
}

impl std::error::Error for AppError {}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, error_type, message) = match &self {
            AppError::OpenAi(msg) => (StatusCode::BAD_GATEWAY, "openai_error", msg.clone()),
            AppError::Validation(msg) => (StatusCode::BAD_REQUEST, "validation_error", msg.clone()),
            AppError::Internal(msg) => (
                StatusCode::INTERNAL_SERVER_ERROR,
                "internal_error",
                msg.clone(),
            ),
        };

        tracing::error!(%error_type, %message, "request failed");

        let body = json!({
            "error": {
                "type": error_type,
                "message": message,
            }
        });

        (status, Json(body)).into_response()
    }
}

// ── Convenient From impls ────────────────────────────────────────────

impl From<reqwest::Error> for AppError {
    fn from(err: reqwest::Error) -> Self {
        AppError::OpenAi(err.to_string())
    }
}

impl From<serde_json::Error> for AppError {
    fn from(err: serde_json::Error) -> Self {
        AppError::Internal(format!("JSON serialization error: {err}"))
    }
}
