from app.services.llm_gateway import model_registry_snapshot, resolve_model_profile, select_model_key_for_workflow


def test_model_registry_snapshot_exposes_capabilities():
    snapshot = model_registry_snapshot()

    assert snapshot["fast"]["capabilities"] == ["fast_chat", "staff_drafting"]
    assert "analyst" in snapshot["deep"]["capabilities"]
    assert "vision_ocr" in snapshot["vision"]["capabilities"]
    assert snapshot["fast"]["label"] == "LipiFast"
    assert snapshot["fast"]["model"] == "LipiFast"
    assert snapshot["deep"]["label"] == "LipiCore"
    assert snapshot["deep"]["model"] == "LipiCore"
    assert snapshot["vision"]["label"] == "LipiCore"
    assert snapshot["vision"]["model"] == "LipiCore"
    assert snapshot["fast"]["enabled"] is True
    assert snapshot["fast"]["context_window_tokens"] >= 8192
    assert snapshot["deep"]["context_window_tokens"] >= snapshot["fast"]["context_window_tokens"]


def test_route_policy_sends_high_risk_workflows_to_deep_model():
    assert select_model_key_for_workflow("ask_knowledge") == "fast"
    assert select_model_key_for_workflow("approved_knowledge") == "deep"
    assert select_model_key_for_workflow("compliance_review") == "deep"
    assert select_model_key_for_workflow("loan_support") == "deep"
    assert select_model_key_for_workflow("vision_ocr") == "vision"
    assert select_model_key_for_workflow("scanned_pdf") == "vision"


def test_resolve_model_profile_accepts_registry_key_and_alias():
    assert resolve_model_profile("fast").key == "fast"
    assert resolve_model_profile("LipiFast").key == "fast"
    assert resolve_model_profile("gemma").key == "fast"
    assert resolve_model_profile("Gemma-4").key == "deep"
    assert resolve_model_profile("analyst").key == "deep"
    assert resolve_model_profile("LipiCore").key == "deep"
    assert resolve_model_profile("legacy-vendor-image-route").key == "fast"
    assert resolve_model_profile("approved_knowledge").context_window_tokens >= 8192
