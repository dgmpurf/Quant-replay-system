"""Local deterministic conversational facade for single-symbol advisory answers."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.config import AdvisoryConversationSettings, Settings, load_settings
from quant_replay_system.signal_semantics import build_signal_semantics_provenance
from quant_replay_system.single_symbol_advisory import (
    SingleSymbolAdvisoryAnswerResult,
    SingleSymbolAdvisoryResult,
    build_single_symbol_advisory,
    build_single_symbol_advisory_answer,
)


ADVISORY_CONVERSATION_KNOWN_LIMITATIONS = [
    "Advisory conversation v0.1 uses deterministic local parsing only.",
    "The conversation facade is not an LLM chat system and does not call external APIs.",
    "The facade routes to local single-symbol advisory artifacts; it does not fetch data.",
    "Demo artifacts remain workflow validation only and are not strategy recommendations.",
    "No message delivery, live trading, broker API, or automated order placement is implemented.",
]

_SYMBOL_PATTERN = re.compile(r"(?<!\d)(\d{6})(?!\d)")
_BUY_PATTERN = re.compile(r"(可以买|能不能买|能买吗|该买|买入|买\b|buy|can i buy|should i buy)", re.IGNORECASE)
_SELL_PATTERN = re.compile(r"(可以卖|能不能卖|卖吗|该卖|卖出|卖\b|sell|can i sell|should i sell)", re.IGNORECASE)
_WATCH_PATTERN = re.compile(r"(关注|观察|继续看|看一看|watch|watchlist)", re.IGNORECASE)
_HOLD_PATTERN = re.compile(r"(持有|继续持有|hold)", re.IGNORECASE)


@dataclass(frozen=True)
class AdvisoryConversationRequest:
    question: str
    candidates_path: Path | None = None
    scored_dataset_path: Path | None = None
    factor_dataset_path: Path | None = None
    signals_path: Path | None = None
    metadata_path: Path | None = None
    snapshot_manifest_path: Path | None = None
    answer_style: str = "concise"


@dataclass(frozen=True)
class AdvisoryConversationParseResult:
    original_question: str
    parsed_symbol: str
    parsed_intent: str
    status: str
    parser_type: str
    issue: str = ""


@dataclass(frozen=True)
class AdvisoryConversationResult:
    conversation_run_id: str
    status: str
    original_question: str
    parsed_symbol: str
    parsed_intent: str
    parser_type: str
    advisory_action: str
    semantics_policy_source: str
    semantics_policy_version: str
    semantics_classifier: str
    semantics_settings_profile: str
    semantics_action: str
    semantics_reason: str
    semantics_manual_confirmation_required: bool
    semantics_auto_order_allowed: bool
    semantics_no_live_trading: bool
    semantics_no_broker_api: bool
    answer_summary: str
    linked_advisory_run_id: str
    linked_answer_run_id: str
    linked_answer_markdown_path: str
    linked_answer_json_path: str
    linked_answer_metadata_path: str
    requires_manual_confirmation: bool
    auto_order_allowed: bool
    no_live_trading: bool
    no_broker_api: bool
    no_message_sent: bool
    llm_api_called: bool
    external_api_called: bool
    artifact_paths: dict[str, Path]
    parse_result: AdvisoryConversationParseResult
    advisory_result: SingleSymbolAdvisoryResult | None
    answer_result: SingleSymbolAdvisoryAnswerResult | None
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def parse_advisory_question(question: str, *, parser_type: str = "deterministic_rule_based") -> AdvisoryConversationParseResult:
    """Parse a simple local advisory question without LLM or network calls."""

    question_text = str(question or "").strip()
    if not question_text:
        return AdvisoryConversationParseResult(
            original_question=question_text,
            parsed_symbol="",
            parsed_intent="UNKNOWN",
            status="PARSE_FAILED",
            parser_type=parser_type,
            issue="Question is empty.",
        )
    symbol_match = _SYMBOL_PATTERN.search(question_text)
    if symbol_match is None:
        return AdvisoryConversationParseResult(
            original_question=question_text,
            parsed_symbol="",
            parsed_intent=classify_advisory_question_intent(question_text),
            status="PARSE_FAILED",
            parser_type=parser_type,
            issue="No six-digit symbol was found in the local question.",
        )
    return AdvisoryConversationParseResult(
        original_question=question_text,
        parsed_symbol=symbol_match.group(1),
        parsed_intent=classify_advisory_question_intent(question_text),
        status="PARSED",
        parser_type=parser_type,
    )


def classify_advisory_question_intent(question: str) -> str:
    """Classify a simple Chinese/English advisory intent using deterministic rules."""

    question_text = str(question or "").strip()
    if not question_text:
        return "UNKNOWN"
    if _SELL_PATTERN.search(question_text):
        return "SELL_REVIEW"
    if _BUY_PATTERN.search(question_text):
        return "BUY_REVIEW"
    if _WATCH_PATTERN.search(question_text):
        return "WATCH_REVIEW"
    if _HOLD_PATTERN.search(question_text):
        return "HOLD_REVIEW"
    if "?" in question_text or "？" in question_text:
        return "GENERAL_REVIEW"
    return "UNKNOWN"


def run_advisory_conversation(
    *,
    question: str,
    candidates_path: str | Path | None = None,
    scored_dataset_path: str | Path | None = None,
    factor_dataset_path: str | Path | None = None,
    signals_path: str | Path | None = None,
    metadata_path: str | Path | None = None,
    snapshot_manifest_path: str | Path | None = None,
    answer_style: str | None = None,
    output_dir: str | Path | None = None,
    settings: Settings | AdvisoryConversationSettings | str | Path | None = None,
) -> AdvisoryConversationResult:
    """Route a parsed local question to deterministic single-symbol advisory answer artifacts."""

    project_settings, conversation_settings = _resolve_settings(settings)
    _assert_conversation_safety(conversation_settings)
    normalized_style = str(answer_style or conversation_settings.answer_style or "concise").strip().lower()
    if normalized_style not in {"concise", "detailed"}:
        raise ValueError("answer_style must be 'concise' or 'detailed'")
    effective_output_dir = Path(output_dir) if output_dir is not None else conversation_settings.output_dir

    request = AdvisoryConversationRequest(
        question=str(question or "").strip(),
        candidates_path=_optional_path(candidates_path),
        scored_dataset_path=_optional_path(scored_dataset_path),
        factor_dataset_path=_optional_path(factor_dataset_path),
        signals_path=_optional_path(signals_path),
        metadata_path=_optional_path(metadata_path),
        snapshot_manifest_path=_optional_path(snapshot_manifest_path),
        answer_style=normalized_style,
    )
    parse_result = parse_advisory_question(request.question, parser_type=conversation_settings.parser_type)
    if parse_result.status == "PARSE_FAILED":
        result = _parse_failed_result(
            request=request,
            parse_result=parse_result,
            output_dir=effective_output_dir,
            settings=conversation_settings,
        )
        if project_settings.advisory_conversation.write_artifacts and conversation_settings.write_artifacts:
            write_advisory_conversation_artifacts(result)
        return result

    if not request.candidates_path and not request.scored_dataset_path and not request.signals_path:
        raise ValueError("Provide at least one of candidates_path, scored_dataset_path, or signals_path")

    advisory = build_single_symbol_advisory(
        parse_result.parsed_symbol,
        candidates_path=request.candidates_path,
        scored_dataset_path=request.scored_dataset_path,
        factor_dataset_path=request.factor_dataset_path,
        signals_path=request.signals_path,
        metadata_path=request.metadata_path,
        snapshot_manifest_path=request.snapshot_manifest_path,
        alert_preview=False,
        settings=project_settings,
    )
    answer = build_single_symbol_advisory_answer(
        advisory,
        question=request.question,
        answer_style=normalized_style,
        settings=project_settings,
    )
    conversation_run_id = generate_advisory_conversation_run_id(
        question=request.question,
        parsed_symbol=parse_result.parsed_symbol,
        parsed_intent=parse_result.parsed_intent,
        linked_answer_run_id=answer.answer_run_id,
        config_version=conversation_settings.config_version,
    )
    paths = resolve_advisory_conversation_paths(effective_output_dir, conversation_run_id)
    semantics_provenance = _conversation_semantics_provenance(
        advisory_action=advisory.advisory_action,
        reason=advisory.reason_summary,
        answer=answer,
    )
    result = AdvisoryConversationResult(
        conversation_run_id=conversation_run_id,
        status=advisory.status,
        original_question=request.question,
        parsed_symbol=parse_result.parsed_symbol,
        parsed_intent=parse_result.parsed_intent,
        parser_type=parse_result.parser_type,
        advisory_action=advisory.advisory_action,
        semantics_policy_source=semantics_provenance["semantics_policy_source"],
        semantics_policy_version=semantics_provenance["semantics_policy_version"],
        semantics_classifier=semantics_provenance["semantics_classifier"],
        semantics_settings_profile=semantics_provenance["semantics_settings_profile"],
        semantics_action=semantics_provenance["semantics_action"],
        semantics_reason=semantics_provenance["semantics_reason"],
        semantics_manual_confirmation_required=semantics_provenance["semantics_manual_confirmation_required"],
        semantics_auto_order_allowed=semantics_provenance["semantics_auto_order_allowed"],
        semantics_no_live_trading=semantics_provenance["semantics_no_live_trading"],
        semantics_no_broker_api=semantics_provenance["semantics_no_broker_api"],
        answer_summary=answer.short_answer,
        linked_advisory_run_id=advisory.advisory_run_id,
        linked_answer_run_id=answer.answer_run_id,
        linked_answer_markdown_path=str(answer.artifact_paths.get("single_symbol_advisory_answer", "")),
        linked_answer_json_path=str(answer.artifact_paths.get("single_symbol_advisory_answer_json", "")),
        linked_answer_metadata_path=str(answer.artifact_paths.get("metadata", "")),
        requires_manual_confirmation=True,
        auto_order_allowed=False,
        no_live_trading=True,
        no_broker_api=True,
        no_message_sent=True,
        llm_api_called=False,
        external_api_called=False,
        artifact_paths=paths,
        parse_result=parse_result,
        advisory_result=advisory,
        answer_result=answer,
        known_limitations=ADVISORY_CONVERSATION_KNOWN_LIMITATIONS,
        audit_metadata=_audit_metadata(
            request=request,
            parse_result=parse_result,
            settings=conversation_settings,
            advisory=advisory,
            answer=answer,
        ),
    )
    if project_settings.advisory_conversation.write_artifacts and conversation_settings.write_artifacts:
        write_advisory_conversation_artifacts(result)
    return result


def render_advisory_conversation_report(result: AdvisoryConversationResult) -> str:
    """Render a human-readable local conversation response."""

    lines = [
        f"# Advisory Conversation: {result.parsed_symbol or 'PARSE_FAILED'}",
        "",
        "This is a deterministic local routing layer. It is not an LLM chat system.",
        "It does not fetch data, send messages, place orders, or connect to brokers.",
        "",
        "## Parsed Question",
        "",
        f"- Original question: {result.original_question}",
        f"- Parsed symbol: `{result.parsed_symbol}`",
        f"- Parsed intent: `{result.parsed_intent}`",
        f"- Parser type: `{result.parser_type}`",
        f"- Status: `{result.status}`",
        "",
        "## Local Advisory Answer",
        "",
        f"- Advisory action: `{result.advisory_action}`",
        f"- Answer summary: {result.answer_summary}",
        f"- Linked advisory run id: `{result.linked_advisory_run_id}`",
        f"- Linked answer run id: `{result.linked_answer_run_id}`",
        f"- Linked answer markdown: `{result.linked_answer_markdown_path}`",
    ]
    if result.parse_result.status == "PARSE_FAILED":
        lines.extend(
            [
                "",
                "## Parse Boundary",
                "",
                "I could not find a six-digit local symbol in the question. No symbol or recommendation was invented.",
            ]
        )
    if result.status == "NOT_FOUND":
        lines.extend(
            [
                "",
                "## Missing Symbol Boundary",
                "",
                "The parsed symbol was not present in the provided local artifact. No recommendation was invented.",
            ]
        )
    if result.advisory_result and (
        result.advisory_result.demo_mode
        or result.advisory_result.not_strategy_recommendation
        or result.advisory_action == "DEMO_ONLY"
    ):
        lines.extend(
            [
                "",
                "## Demo Boundary",
                "",
                "This is a demo-only local advisory review. It is not a real trading recommendation.",
            ]
        )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            f"- Manual confirmation required: `{result.requires_manual_confirmation}`",
            f"- Auto-order allowed: `{result.auto_order_allowed}`",
            f"- No live trading: `{result.no_live_trading}`",
            f"- No broker API: `{result.no_broker_api}`",
            f"- No message sent: `{result.no_message_sent}`",
            f"- LLM API called: `{result.llm_api_called}`",
            f"- External API called: `{result.external_api_called}`",
        ]
    )
    return "\n".join(lines)


def write_advisory_conversation_artifacts(result: AdvisoryConversationResult) -> dict[str, Path]:
    """Write local conversation report, JSON, and metadata artifacts."""

    artifact_dir = result.artifact_paths["artifact_dir"]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    report_path = result.artifact_paths["advisory_conversation_report"]
    json_path = result.artifact_paths["advisory_conversation_json"]
    metadata_path = result.artifact_paths["metadata"]
    report_path.write_text(render_advisory_conversation_report(result), encoding="utf-8")
    payload = _conversation_payload(result)
    json_path.write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True), encoding="utf-8")
    metadata_path.write_text(
        json.dumps(_json_safe(build_advisory_conversation_metadata(result)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return result.artifact_paths


def build_advisory_conversation_metadata(result: AdvisoryConversationResult) -> dict[str, Any]:
    """Build metadata.json for the local conversation facade artifact."""

    return {
        "conversation_run_id": result.conversation_run_id,
        "status": result.status,
        "original_question": result.original_question,
        "parsed_symbol": result.parsed_symbol,
        "parsed_intent": result.parsed_intent,
        "parser_type": result.parser_type,
        "advisory_action": result.advisory_action,
        "semantics_policy_source": result.semantics_policy_source,
        "semantics_policy_version": result.semantics_policy_version,
        "semantics_classifier": result.semantics_classifier,
        "semantics_settings_profile": result.semantics_settings_profile,
        "semantics_action": result.semantics_action,
        "semantics_reason": result.semantics_reason,
        "semantics_manual_confirmation_required": result.semantics_manual_confirmation_required,
        "semantics_auto_order_allowed": result.semantics_auto_order_allowed,
        "semantics_no_live_trading": result.semantics_no_live_trading,
        "semantics_no_broker_api": result.semantics_no_broker_api,
        "answer_summary": result.answer_summary,
        "linked_advisory_run_id": result.linked_advisory_run_id,
        "linked_answer_run_id": result.linked_answer_run_id,
        "linked_answer_markdown_path": result.linked_answer_markdown_path,
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
        "llm_api_called": False,
        "external_api_called": False,
        "message_delivery_enabled": False,
        "message_sent": False,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "approved_for_paper_applied": False,
        "output_files": {
            key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"
        },
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
    }


def generate_advisory_conversation_run_id(
    *,
    question: str,
    parsed_symbol: str,
    parsed_intent: str,
    linked_answer_run_id: str,
    config_version: str,
) -> str:
    digest = hashlib.sha256(
        "|".join([question, parsed_symbol, parsed_intent, linked_answer_run_id, config_version]).encode("utf-8")
    ).hexdigest()
    return digest[:12]


def resolve_advisory_conversation_paths(output_dir: str | Path, conversation_run_id: str) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / conversation_run_id
    return {
        "artifact_dir": artifact_dir,
        "advisory_conversation_report": artifact_dir / "advisory_conversation_report.md",
        "advisory_conversation_json": artifact_dir / "advisory_conversation.json",
        "metadata": artifact_dir / "metadata.json",
    }


def _parse_failed_result(
    *,
    request: AdvisoryConversationRequest,
    parse_result: AdvisoryConversationParseResult,
    output_dir: Path,
    settings: AdvisoryConversationSettings,
) -> AdvisoryConversationResult:
    conversation_run_id = generate_advisory_conversation_run_id(
        question=request.question,
        parsed_symbol="",
        parsed_intent=parse_result.parsed_intent,
        linked_answer_run_id="",
        config_version=settings.config_version,
    )
    semantics_provenance = build_signal_semantics_provenance(
        advisory_action="NO_ACTION",
        reason="No row classified; PARSE_FAILED preserved without invented symbol or recommendation.",
        settings_profile="parse_failed",
    )
    return AdvisoryConversationResult(
        conversation_run_id=conversation_run_id,
        status="PARSE_FAILED",
        original_question=request.question,
        parsed_symbol="",
        parsed_intent=parse_result.parsed_intent,
        parser_type=parse_result.parser_type,
        advisory_action="NO_ACTION",
        semantics_policy_source=semantics_provenance["semantics_policy_source"],
        semantics_policy_version=semantics_provenance["semantics_policy_version"],
        semantics_classifier=semantics_provenance["semantics_classifier"],
        semantics_settings_profile=semantics_provenance["semantics_settings_profile"],
        semantics_action=semantics_provenance["semantics_action"],
        semantics_reason=semantics_provenance["semantics_reason"],
        semantics_manual_confirmation_required=semantics_provenance["semantics_manual_confirmation_required"],
        semantics_auto_order_allowed=semantics_provenance["semantics_auto_order_allowed"],
        semantics_no_live_trading=semantics_provenance["semantics_no_live_trading"],
        semantics_no_broker_api=semantics_provenance["semantics_no_broker_api"],
        answer_summary="I could not find a six-digit local symbol in the question. No recommendation was invented.",
        linked_advisory_run_id="",
        linked_answer_run_id="",
        linked_answer_markdown_path="",
        linked_answer_json_path="",
        linked_answer_metadata_path="",
        requires_manual_confirmation=True,
        auto_order_allowed=False,
        no_live_trading=True,
        no_broker_api=True,
        no_message_sent=True,
        llm_api_called=False,
        external_api_called=False,
        artifact_paths=resolve_advisory_conversation_paths(output_dir, conversation_run_id),
        parse_result=parse_result,
        advisory_result=None,
        answer_result=None,
        known_limitations=ADVISORY_CONVERSATION_KNOWN_LIMITATIONS,
        audit_metadata=_audit_metadata(request=request, parse_result=parse_result, settings=settings),
    )


def _audit_metadata(
    *,
    request: AdvisoryConversationRequest,
    parse_result: AdvisoryConversationParseResult,
    settings: AdvisoryConversationSettings,
    advisory: SingleSymbolAdvisoryResult | None = None,
    answer: SingleSymbolAdvisoryAnswerResult | None = None,
) -> dict[str, Any]:
    return {
        "parser_type": settings.parser_type,
        "original_question": request.question,
        "parsed_symbol": parse_result.parsed_symbol,
        "parsed_intent": parse_result.parsed_intent,
        "parse_status": parse_result.status,
        "parse_issue": parse_result.issue,
        "candidates_path": str(request.candidates_path or ""),
        "scored_dataset_path": str(request.scored_dataset_path or ""),
        "signals_path": str(request.signals_path or ""),
        "linked_advisory_run_id": advisory.advisory_run_id if advisory else "",
        "linked_answer_run_id": answer.answer_run_id if answer else "",
        **_conversation_semantics_provenance(
            advisory_action=advisory.advisory_action if advisory else "NO_ACTION",
            reason=advisory.reason_summary
            if advisory
            else "No row classified; PARSE_FAILED preserved without invented symbol or recommendation.",
            answer=answer,
        ),
        "config_version": settings.config_version,
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
        "message_delivery_enabled": False,
        "message_sent": False,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "approved_for_paper_applied": False,
        "external_api_called": False,
        "llm_api_called": False,
    }


def _conversation_payload(result: AdvisoryConversationResult) -> dict[str, Any]:
    return {
        "conversation_run_id": result.conversation_run_id,
        "status": result.status,
        "original_question": result.original_question,
        "parsed_symbol": result.parsed_symbol,
        "parsed_intent": result.parsed_intent,
        "parser_type": result.parser_type,
        "advisory_action": result.advisory_action,
        "semantics_policy_source": result.semantics_policy_source,
        "semantics_policy_version": result.semantics_policy_version,
        "semantics_classifier": result.semantics_classifier,
        "semantics_settings_profile": result.semantics_settings_profile,
        "semantics_action": result.semantics_action,
        "semantics_reason": result.semantics_reason,
        "semantics_manual_confirmation_required": result.semantics_manual_confirmation_required,
        "semantics_auto_order_allowed": result.semantics_auto_order_allowed,
        "semantics_no_live_trading": result.semantics_no_live_trading,
        "semantics_no_broker_api": result.semantics_no_broker_api,
        "answer_summary": result.answer_summary,
        "linked_advisory_run_id": result.linked_advisory_run_id,
        "linked_answer_run_id": result.linked_answer_run_id,
        "linked_answer_markdown_path": result.linked_answer_markdown_path,
        "requires_manual_confirmation": result.requires_manual_confirmation,
        "auto_order_allowed": result.auto_order_allowed,
        "no_live_trading": result.no_live_trading,
        "no_broker_api": result.no_broker_api,
        "no_message_sent": result.no_message_sent,
        "llm_api_called": result.llm_api_called,
        "external_api_called": result.external_api_called,
        "parse_result": result.parse_result.__dict__,
        "audit_metadata": result.audit_metadata,
    }


def _conversation_semantics_provenance(
    *,
    advisory_action: str,
    reason: str,
    answer: SingleSymbolAdvisoryAnswerResult | None = None,
) -> dict[str, Any]:
    if answer is not None and answer.semantics_policy_source:
        return {
            "semantics_policy_source": answer.semantics_policy_source,
            "semantics_policy_version": answer.semantics_policy_version,
            "semantics_classifier": answer.semantics_classifier,
            "semantics_settings_profile": answer.semantics_settings_profile,
            "semantics_action": answer.semantics_action,
            "semantics_reason": answer.semantics_reason,
            "semantics_manual_confirmation_required": answer.semantics_manual_confirmation_required,
            "semantics_auto_order_allowed": answer.semantics_auto_order_allowed,
            "semantics_no_live_trading": answer.semantics_no_live_trading,
            "semantics_no_broker_api": answer.semantics_no_broker_api,
        }
    return build_signal_semantics_provenance(
        advisory_action=advisory_action,
        reason=reason,
        settings_profile="conversation",
    )


def _resolve_settings(
    settings: Settings | AdvisoryConversationSettings | str | Path | None,
) -> tuple[Settings, AdvisoryConversationSettings]:
    if settings is None:
        project_settings = load_settings(Path("config/default.yaml"))
        return project_settings, project_settings.advisory_conversation
    if isinstance(settings, Settings):
        return settings, settings.advisory_conversation
    if isinstance(settings, AdvisoryConversationSettings):
        project_settings = load_settings(Path("config/default.yaml"))
        return project_settings.model_copy(update={"advisory_conversation": settings}), settings
    project_settings = load_settings(settings)
    return project_settings, project_settings.advisory_conversation


def _assert_conversation_safety(settings: AdvisoryConversationSettings) -> None:
    if settings.enable_live_trading or settings.enable_broker_api:
        raise ValueError("Advisory conversation cannot enable live trading or broker API access")
    if settings.enable_message_delivery:
        raise ValueError("Advisory conversation is local only and cannot deliver messages")
    if settings.enable_llm_api:
        raise ValueError("Advisory conversation v0.1 cannot call LLM APIs")
    if settings.auto_order_allowed:
        raise ValueError("Advisory conversation cannot allow automatic order placement")


def _optional_path(value: str | Path | None) -> Path | None:
    if value is None or str(value).strip() == "":
        return None
    return Path(value)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value
