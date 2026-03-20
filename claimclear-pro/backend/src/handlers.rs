use axum::{extract::State, Json};
use chrono::Utc;
use std::sync::Arc;
use tokio::sync::RwLock;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::{
    ClaimRequest, ClaimResponse, ConfigRequest, ConfigStatusResponse, HealthResponse,
    SampleClaim, SamplesResponse,
};
use crate::openai::{compute_comprehension_score, generate_explanation};

/// Shared application state passed to handlers.
pub struct AppState {
    pub openai_api_key: RwLock<Option<String>>,
}

/// POST /api/explain
///
/// Accepts a `ClaimRequest`, calls OpenAI, and returns a `ClaimResponse`.
pub async fn explain_claim(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<ClaimRequest>,
) -> Result<Json<ClaimResponse>, AppError> {
    // ── Validation ───────────────────────────────────────────────
    if payload.claim_id.trim().is_empty() {
        return Err(AppError::Validation("claim_id is required".into()));
    }
    if payload.customer_name.trim().is_empty() {
        return Err(AppError::Validation("customer_name is required".into()));
    }
    if payload.claim_amount <= 0.0 {
        return Err(AppError::Validation(
            "claim_amount must be positive".into(),
        ));
    }
    if payload.decision.trim().is_empty() {
        return Err(AppError::Validation("decision is required".into()));
    }

    let request_id = Uuid::new_v4().to_string();
    let start = std::time::Instant::now();

    tracing::info!(
        request_id = %request_id,
        claim_id = %payload.claim_id,
        "processing claim explanation request"
    );

    // ── Call OpenAI ──────────────────────────────────────────────
    let api_key = state.openai_api_key.read().await;
    let api_key = api_key.as_deref().ok_or_else(|| {
        AppError::Validation("OpenAI API key not configured. Please set it in Settings.".into())
    })?;
    let (explanation, glossary) =
        generate_explanation(api_key, &payload).await?;

    let processing_time_ms = start.elapsed().as_millis() as u64;

    // ── Comprehension score ─────────────────────────────────────
    let comprehension_score = compute_comprehension_score(&explanation);

    tracing::info!(
        request_id = %request_id,
        processing_time_ms,
        comprehension_score,
        glossary_count = glossary.len(),
        "claim explanation generated"
    );

    Ok(Json(ClaimResponse {
        explanation,
        glossary,
        comprehension_score,
        processing_time_ms,
        request_id,
    }))
}

/// GET /api/health
pub async fn health_check() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "ok".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        timestamp: Utc::now().to_rfc3339(),
    })
}

/// GET /api/samples
///
/// Returns pre-filled sample claims so users can try the system quickly.
pub async fn get_samples() -> Json<SamplesResponse> {
    let samples = vec![
        SampleClaim {
            label: "Denied Auto Claim".into(),
            claim_id: "CLM-2024-78432".into(),
            customer_name: "Sarah Johnson".into(),
            policy_type: "Comprehensive Auto Insurance".into(),
            claim_amount: 4250.00,
            decision: "Denied".into(),
            decision_reason: "The vehicle damage occurred while the policyholder was \
                participating in an organized racing event at a private track. Section 4.2(b) \
                of the policy explicitly excludes coverage for damages sustained during \
                competitive motorsport activities, speed tests, or rally events, regardless \
                of whether the event was sanctioned or unsanctioned."
                .into(),
            policy_terms: "Section 4.2(b) - Motorsport Exclusion: No coverage for loss or \
                damage arising from the insured vehicle's participation in any racing, speed \
                contest, demolition contest, or stunting activity. Section 12.1 - General \
                Exclusions apply."
                .into(),
            tone: "empathetic".into(),
            reading_level: "8th grade".into(),
        },
        SampleClaim {
            label: "Approved Health Claim".into(),
            claim_id: "CLM-2024-91205".into(),
            customer_name: "Michael Chen".into(),
            policy_type: "Premium Health Insurance".into(),
            claim_amount: 12800.00,
            decision: "Approved".into(),
            decision_reason: "Emergency appendectomy performed at St. Mary's Hospital is \
                covered under the emergency surgical procedures benefit. The procedure was \
                medically necessary as confirmed by the attending physician. The claim amount \
                falls within the annual surgical benefit limit of $50,000."
                .into(),
            policy_terms: "Section 7.1 - Emergency Surgical Benefits: Covers medically \
                necessary emergency surgeries up to $50,000 per policy year. Section 7.3 - \
                Hospital stay covered at 80% after deductible for up to 30 days."
                .into(),
            tone: "formal".into(),
            reading_level: "professional".into(),
        },
        SampleClaim {
            label: "Partial Home Claim".into(),
            claim_id: "CLM-2024-63891".into(),
            customer_name: "Maria Rodriguez".into(),
            policy_type: "Homeowners Insurance".into(),
            claim_amount: 35000.00,
            decision: "Partially Approved".into(),
            decision_reason: "Water damage to the first floor is covered under the standard \
                perils provision; however, the mold remediation costs ($12,000) are excluded \
                as the mold resulted from long-term moisture accumulation that predates the \
                covered water event. Approved amount: $23,000."
                .into(),
            policy_terms: "Section 3.1 - Covered Perils: Sudden and accidental water damage \
                from burst pipes. Section 3.4(c) - Mold Exclusion: Mold remediation is \
                excluded unless directly and solely caused by a single covered water event \
                occurring within 48 hours."
                .into(),
            tone: "empathetic".into(),
            reading_level: "5th grade".into(),
        },
        SampleClaim {
            label: "Denied Life Claim".into(),
            claim_id: "CLM-2024-44217".into(),
            customer_name: "James Patterson".into(),
            policy_type: "Term Life Insurance".into(),
            claim_amount: 500000.00,
            decision: "Denied".into(),
            decision_reason: "The policy application contained material misrepresentations \
                regarding the insured's medical history. The insured failed to disclose a \
                prior diagnosis of Stage II hypertension and prescribed medication, which \
                would have affected underwriting and premium determination. The policy is \
                within the two-year contestability period."
                .into(),
            policy_terms: "Section 9.1 - Contestability: The company may contest the policy \
                within two years of issuance based on material misrepresentation in the \
                application. Section 9.2 - Material Misrepresentation: Failure to disclose \
                medical conditions that would affect risk assessment."
                .into(),
            tone: "formal".into(),
            reading_level: "8th grade".into(),
        },
    ];

    Json(SamplesResponse { samples })
}

/// POST /api/config
///
/// Accepts an API key and stores it securely in memory.
pub async fn set_config(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<ConfigRequest>,
) -> Result<Json<ConfigStatusResponse>, AppError> {
    let key = payload.openai_api_key.trim().to_string();
    if key.is_empty() {
        return Err(AppError::Validation("API key cannot be empty".into()));
    }

    let mut writer = state.openai_api_key.write().await;
    *writer = Some(key);
    drop(writer);

    tracing::info!("OpenAI API key updated via settings UI");

    Ok(Json(ConfigStatusResponse {
        configured: true,
        masked_key: mask_key(
            state.openai_api_key.read().await.as_deref().unwrap_or(""),
        ),
    }))
}

/// GET /api/config/status
///
/// Returns whether an API key is configured (never reveals the full key).
pub async fn get_config_status(
    State(state): State<Arc<AppState>>,
) -> Json<ConfigStatusResponse> {
    let reader = state.openai_api_key.read().await;
    let (configured, masked) = match reader.as_deref() {
        Some(k) if !k.is_empty() => (true, mask_key(k)),
        _ => (false, String::new()),
    };
    Json(ConfigStatusResponse {
        configured,
        masked_key: masked,
    })
}

/// DELETE /api/config
///
/// Removes the stored API key from memory.
pub async fn delete_config(
    State(state): State<Arc<AppState>>,
) -> Json<ConfigStatusResponse> {
    let mut writer = state.openai_api_key.write().await;
    *writer = None;
    tracing::info!("OpenAI API key removed via settings UI");
    Json(ConfigStatusResponse {
        configured: false,
        masked_key: String::new(),
    })
}

/// Show only the first 3 and last 4 characters of a key.
fn mask_key(key: &str) -> String {
    if key.len() <= 8 {
        return "*".repeat(key.len());
    }
    let prefix = &key[..3];
    let suffix = &key[key.len() - 4..];
    format!("{}...{}", prefix, suffix)
}
