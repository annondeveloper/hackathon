use serde::{Deserialize, Serialize};

/// Incoming claim explanation request from the frontend.
#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct ClaimRequest {
    pub claim_id: String,
    pub customer_name: String,
    pub policy_type: String,
    pub claim_amount: f64,
    pub decision: String,
    pub decision_reason: String,
    pub policy_terms: String,
    /// Desired tone: "empathetic", "formal", "simple"
    pub tone: String,
    /// Target reading level: "5th grade", "8th grade", "professional"
    pub reading_level: String,
}

/// Response returned to the frontend after processing.
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ClaimResponse {
    pub explanation: String,
    pub glossary: Vec<GlossaryTerm>,
    pub comprehension_score: f64,
    pub processing_time_ms: u64,
    pub request_id: String,
}

/// A single glossary entry extracted from the explanation.
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct GlossaryTerm {
    pub term: String,
    pub definition: String,
}

/// Pre-filled sample claim for demonstration purposes.
#[derive(Debug, Serialize, Clone)]
pub struct SampleClaim {
    pub claim_id: String,
    pub customer_name: String,
    pub policy_type: String,
    pub claim_amount: f64,
    pub decision: String,
    pub decision_reason: String,
    pub policy_terms: String,
    pub tone: String,
    pub reading_level: String,
    pub label: String,
}

/// Health-check response payload.
#[derive(Debug, Serialize)]
pub struct HealthResponse {
    pub status: String,
    pub version: String,
    pub timestamp: String,
}

/// Wrapper for the samples endpoint.
#[derive(Debug, Serialize)]
pub struct SamplesResponse {
    pub samples: Vec<SampleClaim>,
}

// ── Config DTOs ──────────────────────────────────────────────────────

#[derive(Debug, Deserialize)]
pub struct ConfigRequest {
    pub openai_api_key: String,
}

#[derive(Debug, Serialize)]
pub struct ConfigStatusResponse {
    pub configured: bool,
    pub masked_key: String,
}

// ── OpenAI DTOs ──────────────────────────────────────────────────────

#[derive(Debug, Serialize)]
pub struct OpenAiRequest {
    pub model: String,
    pub messages: Vec<OpenAiMessage>,
    pub temperature: f64,
    pub max_tokens: u32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct OpenAiMessage {
    pub role: String,
    pub content: String,
}

#[derive(Debug, Deserialize)]
pub struct OpenAiResponse {
    pub choices: Vec<OpenAiChoice>,
    pub usage: Option<OpenAiUsage>,
}

#[derive(Debug, Deserialize)]
pub struct OpenAiChoice {
    pub message: OpenAiMessage,
}

#[derive(Debug, Deserialize)]
pub struct OpenAiUsage {
    pub prompt_tokens: u32,
    pub completion_tokens: u32,
    pub total_tokens: u32,
}

/// Intermediate structure we ask the model to return as JSON.
#[derive(Debug, Deserialize)]
pub struct AiExplanationPayload {
    pub explanation: String,
    pub glossary: Vec<GlossaryTerm>,
}
