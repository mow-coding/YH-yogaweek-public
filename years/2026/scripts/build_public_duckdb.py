from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ONSTUDIO_DIR = ROOT / "data" / "processed" / "onstudio" / "public"
PUBLIC_OBUD_DIR = ROOT / "data" / "processed" / "obud_reviews" / "public"
PUBLIC_ANALYSIS_DIR = ROOT / "data" / "processed" / "analysis" / "public"
PUBLIC_EXTERNAL_DIR = ROOT / "data" / "external"
DATABASE_DIR = ROOT / "data" / "database"
DATABASE_PATH = DATABASE_DIR / "yogaweek_public.duckdb"

REQUIRED_TABLES = {
    "onstudio_classes": PUBLIC_ONSTUDIO_DIR / "onstudio_classes_2026_yeonhui_yoga_week.csv",
    "onstudio_reservations": PUBLIC_ONSTUDIO_DIR
    / "onstudio_reservation_2026_yeonhui_yoga_week_deidentified.csv",
    "onstudio_cancellations": PUBLIC_ONSTUDIO_DIR
    / "onstudio_cancel_2026_yeonhui_yoga_week_deidentified.csv",
}

OPTIONAL_TABLES = {
    "obud_reviews": PUBLIC_OBUD_DIR / "obud_reviews_deidentified.csv",
    "class_hype_metrics": PUBLIC_ANALYSIS_DIR / "class_hype_metrics.csv",
    "studio_hype_metrics": PUBLIC_ANALYSIS_DIR / "studio_hype_metrics.csv",
    "class_hype_gis": PUBLIC_ANALYSIS_DIR / "class_hype_gis.csv",
    "studio_hype_gis": PUBLIC_ANALYSIS_DIR / "studio_hype_gis.csv",
    "event_location_catalog_gis": PUBLIC_ANALYSIS_DIR / "event_location_catalog_gis.csv",
    "location_nodes": PUBLIC_ANALYSIS_DIR / "location_nodes.csv",
    "location_distance_matrix": PUBLIC_ANALYSIS_DIR / "location_distance_matrix.csv",
    "class_location_evidence": PUBLIC_ANALYSIS_DIR / "class_location_evidence_public.csv",
    "class_schedule_gis": PUBLIC_ANALYSIS_DIR / "class_schedule_gis.csv",
    "transition_feasibility_public": PUBLIC_ANALYSIS_DIR / "transition_feasibility_public.csv",
    "location_transition_feasibility_public": PUBLIC_ANALYSIS_DIR
    / "location_transition_feasibility_public.csv",
    "studio_locations": PUBLIC_EXTERNAL_DIR / "studio_locations_public.csv",
    "ticket_price_reference": PUBLIC_ANALYSIS_DIR / "ticket_price_reference.csv",
    "obud_settlement_rules": PUBLIC_ANALYSIS_DIR / "obud_settlement_rules.csv",
    "obud_pass_settlement_table": PUBLIC_ANALYSIS_DIR / "obud_pass_settlement_table.csv",
    "obud_settlement_estimate_by_class": PUBLIC_ANALYSIS_DIR
    / "obud_settlement_estimate_by_class.csv",
    "obud_settlement_estimate_by_studio_month": PUBLIC_ANALYSIS_DIR
    / "obud_settlement_estimate_by_studio_month.csv",
    "obud_pass_package_inference_summary": PUBLIC_ANALYSIS_DIR
    / "obud_pass_package_inference_summary.csv",
    "notion_shared_page_summary": PUBLIC_ANALYSIS_DIR
    / "notion_shared_page_summary_public.csv",
    "notion_shared_communication_theme_summary": PUBLIC_ANALYSIS_DIR
    / "notion_shared_communication_theme_summary_public.csv",
    "google_drive_program_capacity_reference": PUBLIC_ANALYSIS_DIR
    / "google_drive_program_capacity_reference.csv",
    "onstudio_calendar_capacity_reference": PUBLIC_ANALYSIS_DIR
    / "onstudio_calendar_capacity_reference.csv",
    "capacity_reference_comparison": PUBLIC_ANALYSIS_DIR
    / "capacity_reference_comparison.csv",
    "class_capacity_hype_metrics": PUBLIC_ANALYSIS_DIR / "class_capacity_hype_metrics.csv",
    "studio_capacity_hype_metrics": PUBLIC_ANALYSIS_DIR / "studio_capacity_hype_metrics.csv",
    "google_drive_archive_area_summary": PUBLIC_ANALYSIS_DIR / "google_drive_archive_area_summary.csv",
    "google_drive_archive_asset_type_summary": PUBLIC_ANALYSIS_DIR
    / "google_drive_archive_asset_type_summary.csv",
    "google_drive_archive_analysis_opportunity_matrix": PUBLIC_ANALYSIS_DIR
    / "google_drive_archive_analysis_opportunity_matrix.csv",
    "fnb_partner_brands_public": PUBLIC_ANALYSIS_DIR / "fnb_partner_brands_public.csv",
    "sponsor_asset_inventory_public": PUBLIC_ANALYSIS_DIR / "sponsor_asset_inventory_public.csv",
    "viral_mentions_public": PUBLIC_ANALYSIS_DIR / "yeonhui_yoga_week_viral_mentions_public.csv",
    "viral_overall_summary": PUBLIC_ANALYSIS_DIR / "yeonhui_yoga_week_viral_overall_summary.csv",
    "viral_platform_metrics": PUBLIC_ANALYSIS_DIR / "yeonhui_yoga_week_viral_platform_metrics.csv",
    "viral_studio_metrics": PUBLIC_ANALYSIS_DIR / "yeonhui_yoga_week_viral_studio_metrics.csv",
    "viral_unmatched_mentions_public": PUBLIC_ANALYSIS_DIR
    / "yeonhui_yoga_week_viral_unmatched_mentions_public.csv",
    "naver_blog_body_theme_summary": PUBLIC_ANALYSIS_DIR
    / "yeonhui_yoga_week_naver_blog_body_theme_summary.csv",
    "naver_blog_body_studio_summary": PUBLIC_ANALYSIS_DIR
    / "yeonhui_yoga_week_naver_blog_body_studio_summary.csv",
    "naver_blog_body_deep_features_public": PUBLIC_ANALYSIS_DIR
    / "yeonhui_yoga_week_naver_blog_body_deep_features_public.csv",
    "naver_blog_body_post_type_summary": PUBLIC_ANALYSIS_DIR
    / "yeonhui_yoga_week_naver_blog_body_post_type_summary.csv",
    "naver_blog_body_quality_summary": PUBLIC_ANALYSIS_DIR
    / "yeonhui_yoga_week_naver_blog_body_quality_summary.csv",
}


def sql_string(path: Path) -> str:
    return path.as_posix().replace("'", "''")


def csv_reader_sql(path: Path) -> str:
    return (
        f"read_csv('{sql_string(path)}', "
        "header = true, delim = ',', quote = '\"', escape = '\"', strict_mode = false)"
    )


def main() -> None:
    try:
        import duckdb
    except ImportError as exc:
        raise SystemExit(
            "duckdb 패키지가 필요하다. 먼저 `pip install duckdb`를 실행한 뒤 다시 시도한다."
        ) from exc

    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(DATABASE_PATH)) as conn:
        created_tables: list[str] = []

        for table_name, csv_path in REQUIRED_TABLES.items():
            if not csv_path.exists():
                raise FileNotFoundError(f"Missing input CSV: {csv_path}")

            conn.execute(
                f"""
                CREATE OR REPLACE TABLE {table_name} AS
                SELECT *
                FROM {csv_reader_sql(csv_path)}
                """
            )
            created_tables.append(table_name)

        for table_name, csv_path in OPTIONAL_TABLES.items():
            if not csv_path.exists():
                continue

            conn.execute(
                f"""
                CREATE OR REPLACE TABLE {table_name} AS
                SELECT *
                FROM {csv_reader_sql(csv_path)}
                """
            )
            created_tables.append(table_name)

        summary_queries = [
            f"SELECT '{table_name}' AS table_name, count(*) AS rows FROM {table_name}"
            for table_name in created_tables
        ]
        summary = conn.execute(" UNION ALL ".join(summary_queries)).fetchall()

    print(f"Created {DATABASE_PATH}")
    for table_name, rows in summary:
        print(f"{table_name}: {rows}")


if __name__ == "__main__":
    main()
