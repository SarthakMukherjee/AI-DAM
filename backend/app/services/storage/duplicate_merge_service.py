from copy import deepcopy

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.asset.asset_model import Asset

from app.ai.retrieval.semantic_search_service import (
    SemanticSearchService
)

from app.ai.vectorstore.vector_delete_service import (
    VectorDeleteService
) 


class DuplicateMergeService:
    """
    Handles duplicate resolution workflow.

    Responsibilities
    ----------------
    • Merge metadata
    • Merge AI enrichment
    • Merge SQL searchable fields
    • Retire/Delete duplicate
    • Return updated canonical asset

    NOTE:
    Chroma synchronization is intentionally NOT performed here.
    It will be added in Phase 2.4.4.
    """

    @staticmethod
    def _unique(items: list) -> list:
        """
        Removes duplicates while preserving order.
        """
        seen = set()
        output = []

        for item in items:
            if item is None:
                continue

            value = str(item).strip()

            if not value:
                continue

            if value.lower() in seen:
                continue

            seen.add(value.lower())
            output.append(value)

        return output

    @classmethod
    def _merge_metadata(
        cls,
        canonical: Asset,
        duplicate: Asset
    ) -> None:
        """
        Merge duplicate metadata into canonical asset.
        """

        canonical_meta = deepcopy(canonical.asset_metadata or {})
        duplicate_meta = deepcopy(duplicate.asset_metadata or {})

        # -------------------------------------------------
        # CONTENT KEYWORDS
        # -------------------------------------------------

        canonical_keywords = (
            canonical_meta
            .get("content", {})
            .get("keywords", [])
        )

        duplicate_keywords = (
            duplicate_meta
            .get("content", {})
            .get("keywords", [])
        )

        merged_keywords = cls._unique(
            canonical_keywords + duplicate_keywords
        )

        canonical_meta.setdefault(
            "content",
            {}
        )["keywords"] = merged_keywords

        # -------------------------------------------------
        # AI TAGS
        # -------------------------------------------------

        canonical_ai = canonical_meta.setdefault(
            "ai_enrichment",
            {}
        )

        duplicate_ai = duplicate_meta.get(
            "ai_enrichment",
            {}
        )

        canonical_ai_tags = canonical_ai.get(
            "ai_tags",
            []
        )

        duplicate_ai_tags = duplicate_ai.get(
            "ai_tags",
            []
        )

        merged_ai_tags = cls._unique(
            canonical_ai_tags + duplicate_ai_tags
        )

        canonical_ai["ai_tags"] = merged_ai_tags

        # -------------------------------------------------
        # SEARCHABLE TAGS
        # -------------------------------------------------

        merged_searchable = cls._unique(
            canonical_ai.get(
                "searchable_tags",
                []
            ) +
            duplicate_ai.get(
                "searchable_tags",
                []
            )
        )

        canonical_ai["searchable_tags"] = merged_searchable

        # -------------------------------------------------
        # DETECTED OBJECTS
        # -------------------------------------------------

        merged_objects = cls._unique(
            canonical_ai.get(
                "detected_objects",
                []
            ) +
            duplicate_ai.get(
                "detected_objects",
                []
            )
        )

        canonical_ai["detected_objects"] = merged_objects

        canonical.asset_metadata = canonical_meta

        # -------------------------------------------------
        # QUERYABLE SQL COLUMNS
        # -------------------------------------------------

        canonical.ai_tags = merged_ai_tags

        canonical.detected_objects = merged_objects

    @classmethod
    def resolve(
        cls,
        db: Session,
        canonical_asset_id: str,
        duplicate_asset_id: str,
        action: str,
        merge_metadata: bool = True,
    ) -> Asset:
        """
        Resolve duplicate asset.

        Parameters
        ----------
        canonical_asset_id
            Asset to keep.

        duplicate_asset_id
            Asset to retire/delete.

        action
            retire | delete

        merge_metadata
            Merge AI metadata before removal.
        """

        if canonical_asset_id == duplicate_asset_id:
            raise HTTPException(
                status_code=400,
                detail="Canonical and duplicate assets cannot be the same."
            )

        canonical = (
            db.query(Asset)
            .filter(Asset.id == canonical_asset_id)
            .first()
        )

        if canonical is None:
            raise HTTPException(
                status_code=404,
                detail="Canonical asset not found."
            )

        duplicate = (
            db.query(Asset)
            .filter(Asset.id == duplicate_asset_id)
            .first()
        )

        if duplicate is None:
            raise HTTPException(
                status_code=404,
                detail="Duplicate asset not found."
            )

        # ---------------------------------------------
        # MERGE METADATA
        # ---------------------------------------------

        if merge_metadata:
            cls._merge_metadata(
                canonical,
                duplicate,
            )
        
        # Persist merged metadata before re-indexing
        db.flush()

        # ---------------------------------------------
        # RETIRE
        # ---------------------------------------------

        if action == "retire":

            duplicate.status = "retired"

            duplicate.is_latest = False

        # ---------------------------------------------
        # DELETE
        # ---------------------------------------------

        elif action == "delete":

            duplicate_id=duplicate.id
            db.delete(duplicate)

        else:

            raise HTTPException(
                status_code=400,
                detail="Action must be either 'retire' or 'delete'."
            )

        db.commit()

        db.refresh(canonical)

        # -------------------------------------------------
        # Re-index canonical asset in ChromaDB
        # -------------------------------------------------

        SemanticSearchService.reindex_asset(
            asset_id=canonical.id,
            asset_metadata=canonical.asset_metadata or {},
            status=canonical.status
        )

        # -------------------------------------------------
        # Remove duplicate vector if permanently deleted
        # -------------------------------------------------

        if action=="delete":
            VectorDeleteService.delete_asset(
                duplicate_id
            )
        return canonical