"""Package-local CLI for synthetic and governed non-live registry workflows."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from .health import registry_health
from .index import regenerate_index, verify_index
from .models import (
    GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE,
    SYNTHETIC_MODE,
    HumanReviewPayload,
    RegistryError,
)
from .path_safety import derive_receipt_key, derive_subject_key
from .real_candidate import AUTHORITY_PRESENT_STOP, dry_run_real_candidate
from .real_candidate_materialization import materialize_real_candidate
from .review_zip import build_deterministic_review_zip, collect_relative_files
from .transaction import materialize_synthetic
from .verification import preflight_next_task, verify_entry


def _emit(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


def _add_registry_roots(parser: argparse.ArgumentParser, *, allow_candidate_mode: bool = True) -> None:
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--approved-admin-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--protected-root", type=Path, action="append", default=[])
    parser.add_argument("--expected-registry-root", type=Path)
    if allow_candidate_mode:
        parser.add_argument(
            "--registry-mode",
            choices=(SYNTHETIC_MODE, GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE),
            default=SYNTHETIC_MODE,
        )


def _registry_authority(args: argparse.Namespace) -> dict[str, Any]:
    authority = {
        "approved_admin_root": args.approved_admin_root,
        "repository_root": args.repository_root,
        "protected_roots": tuple(args.protected_root),
        "expected_registry_root": args.expected_registry_root,
    }
    if hasattr(args, "registry_mode"):
        authority["registry_mode"] = args.registry_mode
    return authority


def _materialized_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RegistryError("HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP", "materialized-at must be ISO-8601") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="accepted-lineage-registry",
        description="Accepted-lineage validation with synthetic and governed non-live candidate modes",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    derive = subparsers.add_parser("derive-keys")
    derive.add_argument("--subject-phase-id", required=True)
    derive.add_argument("--receipt-id", required=True)

    validate = subparsers.add_parser("validate-review")
    validate.add_argument("--payload", type=Path, required=True)

    materialize = subparsers.add_parser("materialize-synthetic")
    _add_registry_roots(materialize, allow_candidate_mode=False)
    materialize.add_argument("--payload", type=Path, required=True)
    materialize.add_argument("--subject-manifest", type=Path, required=True)
    materialize.add_argument("--subject-packet", type=Path, required=True)
    materialize.add_argument("--subject-artifact-root", type=Path, required=True)
    materialize.add_argument("--review-receipt", type=Path, required=True)
    materialize.add_argument("--materialization-authorization-id", required=True)
    materialize.add_argument("--operator-alias", default="synthetic-codex")
    materialize.add_argument("--operation-id")
    materialize.add_argument("--materialized-at")

    verify = subparsers.add_parser("verify-entry")
    _add_registry_roots(verify)
    verify.add_argument("--subject-key", required=True)
    verify.add_argument("--receipt-key", required=True)
    verify.add_argument("--subject-packet", type=Path, required=True)
    verify.add_argument("--subject-artifact-root", type=Path, required=True)

    rebuild = subparsers.add_parser("rebuild-index")
    _add_registry_roots(rebuild)

    health = subparsers.add_parser("health")
    _add_registry_roots(health)

    preflight = subparsers.add_parser("preflight-next-task")
    _add_registry_roots(preflight)
    preflight.add_argument("--subject-key", required=True)
    preflight.add_argument("--receipt-key", required=True)
    preflight.add_argument("--current-task-approval-id")

    package = subparsers.add_parser("package-review")
    package.add_argument("--source-root", type=Path, required=True)
    package.add_argument("--zip", type=Path, required=True)
    package.add_argument("--approved-admin-root", type=Path, required=True)
    package.add_argument("--repository-root", type=Path, required=True)
    package.add_argument("--protected-root", type=Path, action="append", default=[])
    package.add_argument("--expected-review-output-root", type=Path)
    package.add_argument("--expected-zip", type=Path)

    candidate = subparsers.add_parser("dry-run-real-candidate")
    candidate.add_argument("--candidate-root", type=Path, required=True)
    candidate.add_argument("--approved-admin-root", type=Path, required=True)
    candidate.add_argument("--repository-root", type=Path, required=True)
    candidate.add_argument("--expected-candidate-root", type=Path, required=True)
    candidate.add_argument("--payload", type=Path, required=True)
    candidate.add_argument("--subject-manifest", type=Path, required=True)
    candidate.add_argument("--subject-packet", type=Path, required=True)
    candidate.add_argument("--subject-artifact-root", type=Path, required=True)
    candidate.add_argument("--review-receipt", type=Path, required=True)
    candidate.add_argument("--expected-review-decision-id", required=True)
    candidate.add_argument("--expected-payload-sha256", required=True)
    candidate.add_argument("--expected-subject-manifest-sha256", required=True)
    candidate.add_argument("--expected-review-receipt-sha256", required=True)
    candidate.add_argument("--materialization-authorization-id")

    real_materialize = subparsers.add_parser("materialize-real-candidate")
    real_materialize.add_argument("--root", type=Path, required=True)
    real_materialize.add_argument("--approved-admin-root", type=Path, required=True)
    real_materialize.add_argument("--repository-root", type=Path, required=True)
    real_materialize.add_argument("--expected-candidate-root", type=Path, required=True)
    real_materialize.add_argument("--future-live-registry-root", type=Path, required=True)
    real_materialize.add_argument("--protected-root", type=Path, action="append", default=[])
    real_materialize.add_argument("--payload", type=Path, required=True)
    real_materialize.add_argument("--subject-manifest", type=Path, required=True)
    real_materialize.add_argument("--subject-packet", type=Path, required=True)
    real_materialize.add_argument("--subject-artifact-root", type=Path, required=True)
    real_materialize.add_argument("--review-receipt", type=Path, required=True)
    real_materialize.add_argument("--expected-review-decision-id", required=True)
    real_materialize.add_argument("--expected-payload-sha256", required=True)
    real_materialize.add_argument("--expected-subject-manifest-sha256", required=True)
    real_materialize.add_argument("--expected-review-receipt-sha256", required=True)
    real_materialize.add_argument("--materialization-authorization-id", required=True)
    real_materialize.add_argument("--expected-materialization-authorization-id", required=True)
    real_materialize.add_argument("--operator-alias", required=True)
    real_materialize.add_argument("--operation-id", required=True)
    real_materialize.add_argument("--materialized-at", required=True)
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "derive-keys":
            _emit({"subject_key": derive_subject_key(args.subject_phase_id), "receipt_key": derive_receipt_key(args.receipt_id)})
        elif args.command == "validate-review":
            payload = HumanReviewPayload.from_bytes(args.payload.read_bytes())
            payload.assert_synthetic_only()
            _emit({"status": "PASS", "receipt_id": payload.receipt_id, "subject_phase_id": payload.subject_phase_id})
        elif args.command == "materialize-synthetic":
            result = materialize_synthetic(
                args.root,
                subject_packet_path=args.subject_packet,
                subject_artifact_root=args.subject_artifact_root,
                human_review_payload_bytes=args.payload.read_bytes(),
                subject_artifact_manifest_bytes=args.subject_manifest.read_bytes(),
                review_receipt_bytes=args.review_receipt.read_bytes(),
                materialization_authorization_id=args.materialization_authorization_id,
                operator_alias=args.operator_alias,
                operation_id=args.operation_id,
                materialized_at=_materialized_at(args.materialized_at),
                **_registry_authority(args),
            )
            _emit(result.to_dict())
        elif args.command == "verify-entry":
            _emit(
                verify_entry(
                    args.root,
                    args.subject_key,
                    args.receipt_key,
                    subject_packet_path=args.subject_packet,
                    subject_artifact_root=args.subject_artifact_root,
                    **_registry_authority(args),
                )
            )
        elif args.command == "rebuild-index":
            _emit(regenerate_index(args.root, **_registry_authority(args)))
        elif args.command == "health":
            _emit(registry_health(args.root, **_registry_authority(args)).to_dict())
        elif args.command == "preflight-next-task":
            _emit(
                preflight_next_task(
                    args.root,
                    args.subject_key,
                    args.receipt_key,
                    current_task_approval_id=args.current_task_approval_id,
                    **_registry_authority(args),
                ).to_dict()
            )
        elif args.command == "package-review":
            review_authority = {
                "approved_admin_root": args.approved_admin_root,
                "repository_root": args.repository_root,
                "protected_roots": tuple(args.protected_root),
                "expected_review_output_root": args.expected_review_output_root,
            }
            relative_files = collect_relative_files(args.source_root, **review_authority)
            _emit(
                build_deterministic_review_zip(
                    args.source_root,
                    args.zip,
                    relative_files,
                    expected_zip_path=args.expected_zip,
                    **review_authority,
                ).to_dict()
            )
        elif args.command == "dry-run-real-candidate":
            if args.materialization_authorization_id is not None:
                raise RegistryError(
                    AUTHORITY_PRESENT_STOP,
                    "A materialization authorization ID is forbidden in dry-run mode",
                )
            _emit(
                dry_run_real_candidate(
                    args.candidate_root,
                    approved_admin_root=args.approved_admin_root,
                    repository_root=args.repository_root,
                    expected_candidate_root=args.expected_candidate_root,
                    human_review_payload_bytes=args.payload.read_bytes(),
                    subject_artifact_manifest_bytes=args.subject_manifest.read_bytes(),
                    subject_packet_path=args.subject_packet,
                    subject_artifact_root=args.subject_artifact_root,
                    review_receipt_bytes=args.review_receipt.read_bytes(),
                    expected_review_decision_id=args.expected_review_decision_id,
                    expected_payload_sha256=args.expected_payload_sha256,
                    expected_subject_manifest_sha256=args.expected_subject_manifest_sha256,
                    expected_review_receipt_sha256=args.expected_review_receipt_sha256,
                ).to_dict()
            )
        elif args.command == "materialize-real-candidate":
            result = materialize_real_candidate(
                args.root,
                approved_admin_root=args.approved_admin_root,
                repository_root=args.repository_root,
                expected_candidate_root=args.expected_candidate_root,
                future_live_registry_root=args.future_live_registry_root,
                protected_roots=tuple(args.protected_root),
                human_review_payload_bytes=args.payload.read_bytes(),
                subject_artifact_manifest_bytes=args.subject_manifest.read_bytes(),
                subject_packet_path=args.subject_packet,
                subject_artifact_root=args.subject_artifact_root,
                review_receipt_bytes=args.review_receipt.read_bytes(),
                expected_review_decision_id=args.expected_review_decision_id,
                expected_payload_sha256=args.expected_payload_sha256,
                expected_subject_manifest_sha256=args.expected_subject_manifest_sha256,
                expected_review_receipt_sha256=args.expected_review_receipt_sha256,
                materialization_authorization_id=args.materialization_authorization_id,
                expected_materialization_authorization_id=args.expected_materialization_authorization_id,
                operator_alias=args.operator_alias,
                operation_id=args.operation_id,
                materialized_at=_materialized_at(args.materialized_at),
            )
            _emit(result.to_dict())
        else:
            raise AssertionError(args.command)
    except RegistryError as exc:
        _emit({"status": "STOP", **exc.to_dict()})
        return 2
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
