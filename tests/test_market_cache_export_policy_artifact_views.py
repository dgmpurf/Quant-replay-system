import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.market_cache_export_policy_health import check_market_cache_export_policy_health
from quant_replay_system.market_cache_export_policy_index import build_market_cache_export_policy_index
from quant_replay_system.market_cache_export_policy_status import run_market_cache_export_policy_status


def test_policy_plan_index_detects_fake_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "market_cache_export_policy"
    paths = _write_fake_policy_plan(root, plan_id="plan-pass")

    result = build_market_cache_export_policy_index(root=root, output_dir=tmp_path / "index", settings=_settings(tmp_path, root))

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0].to_dict()
    assert row["plan_id"] == "plan-pass"
    assert row["status"] == "PASS"
    assert int(row["recommendation_count"]) == 1
    assert int(row["recommended_count"]) == 1
    assert int(row["comparison_pass_count"]) == 1
    assert int(row["comparison_unavailable_count"]) == 0
    assert int(row["comparison_supported_recommendation_count"]) == 1
    assert row["generated_reviewed_manifest_path"] == str(paths["recommended_manifest"])
    assert row["symbols"] == "000001"
    assert result.artifact_paths["market_cache_export_policy_index_csv"].exists()


def test_policy_plan_index_handles_no_artifacts(tmp_path: Path) -> None:
    result = build_market_cache_export_policy_index(
        root=tmp_path / "missing_root",
        output_dir=tmp_path / "index",
        settings=_settings(tmp_path, tmp_path / "missing_root"),
    )

    assert result.artifact_count == 0
    assert result.index_frame.empty
    assert any("root not found" in warning for warning in result.warnings)


def test_policy_plan_health_pass_for_complete_all_recommended_plan(tmp_path: Path) -> None:
    root = tmp_path / "market_cache_export_policy"
    _write_fake_policy_plan(root, plan_id="plan-pass")
    index = build_market_cache_export_policy_index(root=root, output_dir=tmp_path / "index", settings=_settings(tmp_path, root))

    result = check_market_cache_export_policy_health(
        index_df=index.index_frame,
        output_dir=tmp_path / "health",
        settings=_settings(tmp_path, root),
    )

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.issue_count == 0


def test_policy_plan_health_warn_for_provisional_recommendation(tmp_path: Path) -> None:
    root = tmp_path / "market_cache_export_policy"
    _write_fake_policy_plan(
        root,
        plan_id="plan-warn",
        status="WARN",
        rows=[
            _recommendation_row("000001", "RECOMMENDED", "AKSHARE_OPTIONAL", "TENCENT"),
            _recommendation_row(
                "510300",
                "RECOMMENDED_WITH_WARNINGS",
                "AKSHARE_OPTIONAL",
                "SINA",
                warnings="One or more required fields are PROVISIONAL and require review.",
                security_type="ETF",
            ),
        ],
    )

    result = check_market_cache_export_policy_health(root=root, output_dir=tmp_path / "health", settings=_settings(tmp_path, root))

    assert result.status == "WARN"
    assert "PROVISIONAL_RECOMMENDATION" in set(result.health_frame["issue_code"])
    assert "PROVISIONAL_WITHOUT_REFERENCE" in set(result.health_frame["issue_code"])
    assert result.error_count == 0


def test_policy_plan_health_warn_for_stock_comparison_fail(tmp_path: Path) -> None:
    root = tmp_path / "market_cache_export_policy"
    _write_fake_policy_plan(
        root,
        plan_id="plan-comparison-fail",
        status="WARN",
        rows=[
            _recommendation_row(
                "000001",
                "RECOMMENDED_WITH_WARNINGS",
                "AKSHARE_OPTIONAL",
                "TENCENT",
                warnings="Comparison against BAOSTOCK_OPTIONAL/BAOSTOCK failed.",
                comparison_status="FAIL",
            )
        ],
    )

    result = check_market_cache_export_policy_health(root=root, output_dir=tmp_path / "health", settings=_settings(tmp_path, root))

    assert result.status == "WARN"
    assert "ACTIONABLE_COMPARISON_FAILURE" in set(result.health_frame["issue_code"])
    assert result.error_count == 0


def test_policy_plan_artifact_views_handle_older_plan_without_comparison_fields(tmp_path: Path) -> None:
    root = tmp_path / "market_cache_export_policy"
    paths = _write_fake_policy_plan(root, plan_id="plan-old-format")
    _strip_comparison_fields(paths)

    index = build_market_cache_export_policy_index(root=root, output_dir=tmp_path / "index", settings=_settings(tmp_path, root))
    health = check_market_cache_export_policy_health(index_df=index.index_frame, output_dir=tmp_path / "health", settings=_settings(tmp_path, root))

    row = index.index_frame.iloc[0].to_dict()
    assert int(row["comparison_pass_count"]) == 0
    assert health.status == "PASS"
    assert "COMPARISON_MISSING" not in set(health.health_frame["issue_code"])


def test_policy_plan_health_warns_when_new_format_comparison_status_missing(tmp_path: Path) -> None:
    root = tmp_path / "market_cache_export_policy"
    paths = _write_fake_policy_plan(root, plan_id="plan-missing-comparison-status")
    recommendations = pd.read_csv(paths["recommendations"], dtype={"symbol": str})
    recommendations.loc[0, "comparison_status"] = ""
    recommendations.to_csv(paths["recommendations"], index=False)
    metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
    metadata["recommendations"][0]["comparison_status"] = ""
    paths["metadata"].write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")

    result = check_market_cache_export_policy_health(root=root, output_dir=tmp_path / "health", settings=_settings(tmp_path, root))

    assert result.status == "WARN"
    assert "COMPARISON_MISSING" in set(result.health_frame["issue_code"])


def test_policy_plan_health_fail_for_missing_generated_manifest(tmp_path: Path) -> None:
    root = tmp_path / "market_cache_export_policy"
    paths = _write_fake_policy_plan(root, plan_id="plan-missing-manifest")
    paths["recommended_manifest"].unlink()

    result = check_market_cache_export_policy_health(root=root, output_dir=tmp_path / "health", settings=_settings(tmp_path, root))

    assert result.status == "FAIL"
    assert "MISSING_GENERATED_MANIFEST" in set(result.health_frame["issue_code"])


def test_policy_plan_health_fail_when_manifest_lacks_source_upstream(tmp_path: Path) -> None:
    root = tmp_path / "market_cache_export_policy"
    paths = _write_fake_policy_plan(root, plan_id="plan-missing-source")
    manifest = pd.read_csv(paths["recommended_manifest"], dtype={"symbol": str})
    manifest.loc[0, "source"] = ""
    manifest.to_csv(paths["recommended_manifest"], index=False)

    result = check_market_cache_export_policy_health(root=root, output_dir=tmp_path / "health", settings=_settings(tmp_path, root))

    assert result.status == "FAIL"
    assert "MISSING_SOURCE_UPSTREAM_SELECTION" in set(result.health_frame["issue_code"])


def test_policy_plan_health_preserves_leading_zero_symbols_in_manifest_checks(tmp_path: Path) -> None:
    root = tmp_path / "market_cache_export_policy"
    paths = _write_fake_policy_plan(root, plan_id="plan-symbol")

    result = check_market_cache_export_policy_health(root=root, output_dir=tmp_path / "health", settings=_settings(tmp_path, root))
    manifest = pd.read_csv(paths["recommended_manifest"], dtype={"symbol": str})

    assert manifest["symbol"].tolist() == ["000001"]
    assert "SYMBOL_FORMAT_ERROR" not in set(result.health_frame["issue_code"])


def test_policy_plan_status_summarizes_latest_plan(tmp_path: Path) -> None:
    root = tmp_path / "market_cache_export_policy"
    _write_fake_policy_plan(root, plan_id="plan-old", created_at="2024-05-19T00:00:00+00:00")
    _write_fake_policy_plan(root, plan_id="plan-new", created_at="2024-05-20T00:00:00+00:00")

    result = run_market_cache_export_policy_status(root=root, output_dir=tmp_path / "status", config=_settings(tmp_path, root))

    assert result.status == "PASS"
    assert result.latest_plan_id == "plan-new"
    assert result.workflow_stage == "REVIEWED_MANIFEST_READY"
    summary = result.summary_frame.iloc[0].to_dict()
    assert int(summary["comparison_pass_count"]) == 1
    assert int(summary["comparison_unavailable_count"]) == 0
    assert "market-cache-export" in result.next_manual_action


def test_policy_plan_status_flags_comparison_fail_review_stage(tmp_path: Path) -> None:
    root = tmp_path / "market_cache_export_policy"
    _write_fake_policy_plan(
        root,
        plan_id="plan-comparison-fail",
        status="WARN",
        rows=[
            _recommendation_row(
                "000001",
                "RECOMMENDED_WITH_WARNINGS",
                "AKSHARE_OPTIONAL",
                "TENCENT",
                warnings="Comparison against BAOSTOCK_OPTIONAL/BAOSTOCK failed.",
                comparison_status="FAIL",
            )
        ],
    )

    result = run_market_cache_export_policy_status(root=root, output_dir=tmp_path / "status", config=_settings(tmp_path, root))
    summary = result.summary_frame.iloc[0].to_dict()

    assert result.status == "WARN"
    assert result.workflow_stage == "POLICY_PLAN_COMPARISON_WARNINGS_NEED_REVIEW"
    assert int(summary["comparison_fail_count"]) == 1
    assert "source-comparison" in result.next_manual_action


def test_policy_plan_status_handles_no_artifacts(tmp_path: Path) -> None:
    result = run_market_cache_export_policy_status(
        root=tmp_path / "missing_root",
        output_dir=tmp_path / "status",
        config=_settings(tmp_path, tmp_path / "missing_root"),
    )

    assert result.status == "WARN"
    assert result.workflow_stage == "NO_POLICY_PLAN_ARTIFACTS"
    assert result.latest_plan_id == ""


def test_cli_policy_plan_index_health_status_commands(tmp_path: Path, capsys) -> None:
    root = tmp_path / "market_cache_export_policy"
    _write_fake_policy_plan(root, plan_id="plan-cli")

    index_code = cli.main(
        [
            "market-cache-export-plan-index",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "index"),
        ]
    )
    index_output = capsys.readouterr()
    index_csv = tmp_path / "index" / "market_cache_export_policy_index.csv"
    assert index_code == 0
    assert "artifact_count: 1" in index_output.out
    assert "comparison_pass_count: 1" in index_output.out
    assert index_csv.exists()

    health_code = cli.main(
        [
            "market-cache-export-plan-health",
            "--index",
            str(index_csv),
            "--output-dir",
            str(tmp_path / "health"),
        ]
    )
    health_output = capsys.readouterr()
    assert health_code == 0
    assert "Market cache export plan health status: PASS" in health_output.out
    assert "comparison_pass_count: 1" in health_output.out

    status_code = cli.main(
        [
            "market-cache-export-plan-status",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "status"),
        ]
    )
    status_output = capsys.readouterr()
    assert status_code == 0
    assert "workflow_stage: REVIEWED_MANIFEST_READY" in status_output.out
    assert "comparison_pass_count: 1" in status_output.out
    assert "No live trading or broker API was invoked." in status_output.out


def test_policy_plan_artifact_views_are_local_only(tmp_path: Path) -> None:
    root = tmp_path / "market_cache_export_policy"
    _write_fake_policy_plan(root, plan_id="plan-safe")

    index = build_market_cache_export_policy_index(root=root, output_dir=tmp_path / "index", settings=_settings(tmp_path, root))
    health = check_market_cache_export_policy_health(index_df=index.index_frame, output_dir=tmp_path / "health", settings=_settings(tmp_path, root))
    status = run_market_cache_export_policy_status(root=root, output_dir=tmp_path / "status", config=_settings(tmp_path, root))

    assert index.audit_metadata["live_trading_enabled"] is False
    assert index.audit_metadata["broker_api_invoked"] is False
    assert health.audit_metadata["live_trading_enabled"] is False
    assert health.audit_metadata["broker_api_invoked"] is False
    assert status.audit_metadata["live_trading_enabled"] is False
    assert status.audit_metadata["broker_api_invoked"] is False


def _settings(tmp_path: Path, root: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "market_cache_export_policy_index": settings.market_cache_export_policy_index.model_copy(
                update={
                    "root_dir": root,
                    "output_dir": tmp_path / "market_cache_export_policy" / "index",
                }
            ),
            "market_cache_export_policy_health": settings.market_cache_export_policy_health.model_copy(
                update={
                    "root_dir": root,
                    "output_dir": tmp_path / "market_cache_export_policy" / "health",
                    "index_path": tmp_path / "market_cache_export_policy" / "index" / "market_cache_export_policy_index.csv",
                }
            ),
            "market_cache_export_policy_status": settings.market_cache_export_policy_status.model_copy(
                update={
                    "root_dir": root,
                    "output_dir": tmp_path / "market_cache_export_policy" / "status",
                }
            ),
        }
    )


def _write_fake_policy_plan(
    root: Path,
    *,
    plan_id: str,
    status: str = "PASS",
    rows: list[dict] | None = None,
    created_at: str = "2024-05-20T00:00:00+00:00",
) -> dict[str, Path]:
    artifact_dir = root / plan_id
    manifest_dir = root / "_manifests"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    rows = rows or [_recommendation_row("000001", "RECOMMENDED", "AKSHARE_OPTIONAL", "TENCENT")]
    recommendations_path = artifact_dir / "market_cache_export_policy_recommendations.csv"
    issues_path = artifact_dir / "market_cache_export_policy_issues.csv"
    report_path = artifact_dir / "market_cache_export_policy_report.md"
    metadata_path = artifact_dir / "metadata.json"
    recommended_manifest = manifest_dir / f"market_cache_export_recommended_{plan_id}.csv"

    pd.DataFrame(rows).to_csv(recommendations_path, index=False)
    issue_rows = [
        {
            "category": "POLICY_WARNING",
            "severity": "WARN",
            "manifest_row": row["manifest_row"],
            "symbol": row["symbol"],
            "source": row["recommended_source"],
            "upstream_source": row["recommended_upstream_source"],
            "message": row.get("warnings", ""),
            "suggested_action": "Review generated manifest.",
            "no_live_trading": True,
            "no_broker_api": True,
        }
        for row in rows
        if row["status"] == "RECOMMENDED_WITH_WARNINGS"
    ]
    pd.DataFrame(issue_rows, columns=["category", "severity", "manifest_row", "symbol", "source", "upstream_source", "message", "suggested_action", "no_live_trading", "no_broker_api"]).to_csv(issues_path, index=False)
    manifest_rows = [
        {
            "symbol": row["symbol"],
            "start_date": row["start_date"],
            "end_date": row["end_date"],
            "source": row["recommended_source"] if row["status"] in {"RECOMMENDED", "RECOMMENDED_WITH_WARNINGS"} else "",
            "upstream_source": row["recommended_upstream_source"] if row["status"] in {"RECOMMENDED", "RECOMMENDED_WITH_WARNINGS"} else "",
            "enabled": row["status"] in {"RECOMMENDED", "RECOMMENDED_WITH_WARNINGS"},
            "security_type": row["security_type"],
            "require_fields": row["required_fields"],
            "notes": row.get("warnings", ""),
        }
        for row in rows
    ]
    pd.DataFrame(manifest_rows).to_csv(recommended_manifest, index=False)
    report_path.write_text(
        "# Policy-aware Reviewed Cache Export Plan\n\nNo live trading or broker API was invoked.\n",
        encoding="utf-8",
    )
    statuses = pd.Series([row["status"] for row in rows])
    status_counts = {key: int(value) for key, value in statuses.value_counts().to_dict().items()}
    metadata = {
        "plan_id": plan_id,
        "status": status,
        "created_at": created_at,
        "manifest_path": str(root / f"{plan_id}_request.csv"),
        "generated_reviewed_manifest_path": str(recommended_manifest),
        "recommendation_count": int(statuses.isin(["RECOMMENDED", "RECOMMENDED_WITH_WARNINGS"]).sum()),
        "issue_count": len(issue_rows),
        "status_counts": status_counts,
        "recommendations": rows,
        "issues": issue_rows,
        "warnings": [row.get("warnings", "") for row in rows if row.get("warnings")],
        "known_limitations": ["test fixture"],
        "artifact_paths": {
            "artifact_dir": str(artifact_dir),
            "market_cache_export_policy_report": str(report_path),
            "market_cache_export_policy_recommendations": str(recommendations_path),
            "market_cache_export_policy_issues": str(issues_path),
            "metadata": str(metadata_path),
            "recommended_manifest": str(recommended_manifest),
        },
        "audit_metadata": {
            "plan_id": plan_id,
            "cache_mutated": False,
            "market_cache_export_run": False,
        },
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "cache_mutated": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_live_trading_statement": "No live trading or broker API was invoked.",
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "artifact_dir": artifact_dir,
        "metadata": metadata_path,
        "report": report_path,
        "recommendations": recommendations_path,
        "issues": issues_path,
        "recommended_manifest": recommended_manifest,
    }


def _recommendation_row(
    symbol: str,
    status: str,
    source: str,
    upstream_source: str,
    *,
    warnings: str = "",
    security_type: str = "STOCK",
    comparison_status: str | None = None,
) -> dict:
    resolved_comparison_status = comparison_status or ("UNAVAILABLE" if security_type == "ETF" else "PASS")
    comparison_available = resolved_comparison_status != "UNAVAILABLE"
    return {
        "manifest_row": 2 if symbol == "000001" else 3,
        "symbol": symbol,
        "start_date": "2024-01-02",
        "end_date": "2024-01-05" if symbol == "000001" else "2024-05-20",
        "security_type": security_type,
        "required_fields": "close,volume,amount",
        "status": status,
        "recommended_source": source,
        "recommended_upstream_source": upstream_source,
        "row_count": 4 if symbol == "000001" else 89,
        "min_trade_date": "2024-01-02",
        "max_trade_date": "2024-01-05" if symbol == "000001" else "2024-05-20",
        "candidate_count": 1,
        "policy_statuses": "{}",
        "warnings": warnings,
        "reason": "test fixture",
        "notes": "test fixture",
        "comparison_available": comparison_available,
        "comparison_reference_source": "BAOSTOCK_OPTIONAL" if comparison_available else "",
        "comparison_reference_upstream": "BAOSTOCK" if comparison_available else "",
        "comparison_status": resolved_comparison_status,
        "comparison_matched_rows": 4 if comparison_available else 0,
        "comparison_source_only_rows": 0,
        "comparison_max_close_diff_pct": 0.0 if comparison_available else "",
        "comparison_median_volume_ratio": 1.0 if comparison_available else "",
        "comparison_median_amount_ratio": 1.0 if comparison_available else "",
        "comparison_diagnostic_classification": "NO_UNIT_MISMATCH" if comparison_available else "NO_REFERENCE_SOURCE",
        "comparison_warning_reason": "" if comparison_available else "No comparison reference source/upstream is available in cache.",
        "no_live_trading": True,
        "no_broker_api": True,
    }


def _strip_comparison_fields(paths: dict[str, Path]) -> None:
    comparison_columns = [
        "comparison_available",
        "comparison_reference_source",
        "comparison_reference_upstream",
        "comparison_status",
        "comparison_matched_rows",
        "comparison_source_only_rows",
        "comparison_max_close_diff_pct",
        "comparison_median_volume_ratio",
        "comparison_median_amount_ratio",
        "comparison_diagnostic_classification",
        "comparison_warning_reason",
    ]
    recommendations = pd.read_csv(paths["recommendations"], dtype={"symbol": str})
    recommendations = recommendations.drop(columns=[column for column in comparison_columns if column in recommendations.columns])
    recommendations.to_csv(paths["recommendations"], index=False)
    metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
    stripped = []
    for row in metadata["recommendations"]:
        stripped.append({key: value for key, value in row.items() if key not in comparison_columns})
    metadata["recommendations"] = stripped
    paths["metadata"].write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
