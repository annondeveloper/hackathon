use crate::error::AppError;
use crate::models::{
    AiExplanationPayload, ClaimRequest, GlossaryTerm, OpenAiMessage, OpenAiRequest,
    OpenAiResponse, ResponseFormat,
};

/// Concise system prompt — minimises input tokens while preserving accuracy.
/// JSON structure is enforced via OpenAI's response_format, so no schema in the prompt.
fn build_system_prompt() -> String {
    r#"You are ClaimClear AI. Translate insurance claim decisions into clear customer letters.

Rules:
- Address the customer by name; reference their claim ID.
- State the decision, explain why in plain language, cite the provided policy terms only.
- Suggest concrete next steps (appeal, docs, contact).
- Match the requested tone and reading level.
- Do NOT invent policy terms.

Reply as JSON: {"explanation":"<letter text, \\n\\n between paragraphs>","glossary":[{"term":"...","definition":"..."}]}
Include 3–5 glossary entries for jargon a layperson might not know."#
        .to_string()
}

/// Build the user prompt from the incoming claim request.
fn build_user_prompt(req: &ClaimRequest) -> String {
    format!(
        r#"Please explain the following insurance claim decision.

Claim ID: {claim_id}
Customer Name: {customer_name}
Policy Type: {policy_type}
Claim Amount: ${claim_amount:.2}
Decision: {decision}
Decision Reason: {decision_reason}
Relevant Policy Terms: {policy_terms}

Desired tone: {tone}
Target reading level: {reading_level}"#,
        claim_id = req.claim_id,
        customer_name = req.customer_name,
        policy_type = req.policy_type,
        claim_amount = req.claim_amount,
        decision = req.decision,
        decision_reason = req.decision_reason,
        policy_terms = req.policy_terms,
        tone = req.tone,
        reading_level = req.reading_level,
    )
}

/// Call the OpenAI Chat Completions endpoint and return the parsed payload.
pub async fn generate_explanation(
    client: &reqwest::Client,
    api_key: &str,
    claim: &ClaimRequest,
) -> Result<(String, Vec<GlossaryTerm>), AppError> {

    let body = OpenAiRequest {
        model: "gpt-4o-mini".to_string(),
        messages: vec![
            OpenAiMessage {
                role: "system".to_string(),
                content: build_system_prompt(),
            },
            OpenAiMessage {
                role: "user".to_string(),
                content: build_user_prompt(claim),
            },
        ],
        temperature: 0.3,
        max_tokens: 800,
        response_format: Some(ResponseFormat {
            r#type: "json_object".to_string(),
        }),
    };

    let response = client
        .post("https://api.openai.com/v1/chat/completions")
        .header("Authorization", format!("Bearer {api_key}"))
        .json(&body)
        .send()
        .await
        .map_err(|e| AppError::OpenAi(format!("Request failed: {e}")))?;

    if !response.status().is_success() {
        let status = response.status();
        let text = response
            .text()
            .await
            .unwrap_or_else(|_| "unable to read body".into());
        return Err(AppError::OpenAi(format!(
            "OpenAI returned {status}: {text}"
        )));
    }

    let oai_response: OpenAiResponse = response
        .json()
        .await
        .map_err(|e| AppError::OpenAi(format!("Failed to parse OpenAI response: {e}")))?;

    let raw_content = oai_response
        .choices
        .first()
        .map(|c| c.message.content.clone())
        .unwrap_or_default();

    // Try to parse JSON from the model's reply.
    let payload: AiExplanationPayload = serde_json::from_str(&raw_content).map_err(|e| {
        tracing::warn!(raw = %raw_content, "model did not return valid JSON, attempting recovery");
        AppError::OpenAi(format!(
            "Model returned invalid JSON: {e}. Raw response: {raw_content}"
        ))
    })?;

    Ok((payload.explanation, payload.glossary))
}

/// Compute a rough comprehension score (0-100) based on text complexity heuristics.
///
/// The score is higher when the text is easier to read:
/// - Shorter average sentence length → higher score
/// - Fewer long words (proxy for polysyllabic words) → higher score
pub fn compute_comprehension_score(text: &str) -> f64 {
    let sentences: Vec<&str> = text
        .split(|c: char| c == '.' || c == '!' || c == '?')
        .filter(|s| !s.trim().is_empty())
        .collect();

    let sentence_count = sentences.len().max(1) as f64;

    let words: Vec<&str> = text.split_whitespace().collect();
    let word_count = words.len().max(1) as f64;

    let avg_sentence_len = word_count / sentence_count;

    // Count "complex" words (> 6 characters as a proxy for multi-syllable).
    let complex_word_count = words.iter().filter(|w| w.len() > 6).count() as f64;
    let complex_ratio = complex_word_count / word_count;

    // Fog-index-inspired formula, mapped to 0-100.
    let raw = 100.0 - (avg_sentence_len * 1.5 + complex_ratio * 60.0);
    raw.clamp(25.0, 98.0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn simple_text_scores_high() {
        let text = "The sun is up. The cat sat. We are OK. It is fun.";
        let score = compute_comprehension_score(text);
        assert!(score > 70.0, "Simple text should score high, got {score}");
    }

    #[test]
    fn complex_text_scores_lower() {
        let text = "The indemnification provisions notwithstanding, the policyholder's \
                     subrogation rights are fundamentally contingent upon the adjudication \
                     of contributory negligence determinations.";
        let score = compute_comprehension_score(text);
        assert!(score < 70.0, "Complex text should score lower, got {score}");
    }
}
