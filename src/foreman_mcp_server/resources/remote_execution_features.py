"""Resource for listing allowed remote execution features."""

import json
from collections.abc import Sequence

from fastmcp import Context

from foreman_mcp_server.utils.utils import get_foreman_api


def register_remote_execution_features(mcp, allowed_rex_features: Sequence[str] = ()):
    @mcp.resource(
        name="Allowed Remote Execution Features",
        description=(
            "Returns the list of allowed remote execution features. "
            "Only features configured in the server's allowed-rex-features "
            "list are included. Use the job_templates show API to get "
            "template inputs for a specific template."
        ),
        uri="foreman://remote_execution/allowed_features",
        mime_type="application/json",
        enabled=any(allowed_rex_features),
    )
    async def allowed_remote_execution_features_resource(ctx: Context) -> str:
        if not any(allowed_rex_features):
            return json.dumps({"features": [], "allowed_labels": []}, indent=2)

        try:
            api = get_foreman_api(ctx)

            # Fetch all remote execution features from Foreman
            all_features = api.call(
                "remote_execution_features", "index", {"per_page": "all"}
            ).get("results", [])

            # Build lookup by label
            features_by_label = {f.get("label"): f for f in all_features}

            # Fetch all job templates for allowed features in one request
            labels_list = ", ".join(allowed_rex_features)
            search_query = f"feature.label ^ ({labels_list})"
            templates = api.call(
                "job_templates",
                "index",
                {"search": search_query, "per_page": len(allowed_rex_features)},
            ).get("results", [])

            # Build result for each allowed label
            result_features = []
            for label in allowed_rex_features:
                feature = features_by_label.get(label)

                if not feature:
                    # Feature label not found in Foreman
                    result_features.append(
                        _build_feature_entry(
                            label=label, error="Feature not found in Foreman"
                        )
                    )
                    continue

                template_id = feature.get("job_template_id")
                template = next((t for t in templates if t["id"] == template_id), None)

                error = None
                template_name = None

                if not template_id:
                    error = "Feature has no associated job template"
                elif not template:
                    error = f"Job template (id={template_id}) not accessible"
                else:
                    template_name = template.get("name")

                result_features.append(
                    _build_feature_entry(
                        label=label,
                        feature=feature,
                        template_id=template_id,
                        template_name=template_name,
                        error=error,
                    )
                )

            return json.dumps(
                {
                    "features": result_features,
                    "allowed_labels": list(allowed_rex_features),
                },
                indent=2,
            )

        except Exception as e:
            return json.dumps(
                {
                    "features": [],
                    "allowed_labels": list(allowed_rex_features),
                    "error": f"Failed to fetch remote execution features: {e}",
                },
                indent=2,
            )


def _build_feature_entry(
    label: str,
    feature: dict | None = None,
    template_id: int | None = None,
    template_name: str | None = None,
    error: str | None = None,
) -> dict:
    """Build a standardized feature entry for the response."""
    return {
        "label": label,
        "id": feature.get("id") if feature else None,
        "name": feature.get("name") if feature else None,
        "description": feature.get("description") if feature else None,
        "job_template_id": template_id,
        "job_template_name": template_name,
        "error": error,
    }
