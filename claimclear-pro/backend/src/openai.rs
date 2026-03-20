use crate::error::AppError;
use crate::models::{
    AiExplanationPayload, ClaimRequest, GlossaryTerm, OpenAiMessage, OpenAiRequest, OpenAiResponse,
};

/// Build the system prompt that instructs the AI how to produce the explanation.
fn build_system_prompt() -> String {
    r#"You are ClaimClear AI, an expert insurance communication specialist. Your mission
is to translate complex insurance claim decisions into clear, compassionate, and
easily understandable explanations for policyholders.

GUIDELINES:
1. Address the customer by name and reference their specific claim.
2. Clearly state the decision (approved / denied / partially approved).
3. Explain the reasoning using plain language while remaining accurate.
4. Reference relevant policy terms, translating jargon into everyday words.
5. Include next steps the customer can take (appeal, additional documentation, etc.).
6. Maintain the requested tone and reading level throughout.
7. Never invent policy terms that were not provided.
8. Be empathetic — remember the customer may be dealing with a stressful situation.

OUTPUT FORMAT — you MUST reply with valid JSON and nothing else:
{
  "explanation": "<the full explanation as a single string, using paragraphs separated by \\n\\n>",
  "glossary": [
    { "term": "<insurance term used>", "definition": "<plain-language definition>" }
  ]
}

Include 3-6 glossary terms that appear in the explanation. Pick terms a
non-expert might find confusing."#
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
    api_key: &str,
    claim: &ClaimRequest,
) -> Result<(String, Vec<GlossaryTerm>), AppError> {
    let client = reqwest::Client::new();

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
        temperature: 0.5,
        max_tokens: 1500,
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
