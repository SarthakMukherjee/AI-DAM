ai_dam_system/
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   ├── utils/
│   │   └── styles/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/admin_routes.py
|   |   |   ├── asset_routes.py
|   |   |   ├── auth_routes.py 
|   |   |   ├── reviewer_routes.py
|   |   |   ├── search_routes.py
|   |   |   ├── super_admin_routes.py
│   │   │   ├── middleware/
│   │   │   └── dependencies/
|   |   |   |   ├── auth_dependencies.py
|   |   |   |   ├── database.py
│   │   │
│   │   ├── core/
│   │   │   ├── config/
|   |   |   |   ├── settings.py
│   │   │   ├── security/
|   |   |   |   ├──auth.py
|   |   |   |   ├── hashing.py
│   │   │   ├── logging/
│   │   │   └── constants/
│   │   │
│   │   ├── models/
│   │   │   ├── asset/asset_model.py
│   │   │   ├── metadata/
│   │   │   ├── workflow/
│   │   │   ├── user/
|   |   |   |   ├── notofication_model.py 
|   |   |   |   ├── user_model.py
│   │   │   └── analytics/asset_usage_model.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── asset/
│   │   │   ├── metadata/
|   |   |   |   ├── metadata_enums.py
|   |   |   |   ├── metadata_schema.py
│   │   │   ├── user/schemas.py
│   │   │   └── asset_schema.py, search_schema.py
│   │   │
│   │   ├── services/
│   │   │   ├── storage/
|   |   |   |   ├── asset_service.py
|   |   |   |   ├── cloud_service.py
|   |   |   |   ├── pdf_preview_Service.py
|   |   |   |   ├── storage_initializer.py
|   |   |   |   ├── storage_service.py
|   |   |   |   ├── thumbnail_service.py
|   |   |   |   ├── video_preview_service.py
│   │   │   ├── metadata/
│   │   │   ├── workflow/
│   │   │   ├── search/
│   │   │   ├── recommendation/
│   │   │   ├── analytics/
│   │   │   └── versioning/
│   │   │
│   │   ├── ai/
│   │   │   ├── vectorstore/
|   |   |   |   ├── chroma_Service.py
|   |   |   |   ├── vector_collection_service.py
|   |   |   |   ├── vector_query_service.py
|   |   |   |   ├── vector_upsert_service.py
│   │   │   ├── embeddings/
|   |   |   |   ├── embedding_service.py
|   |   |   |   ├── embedding_utils.py
|   |   |   |   ├── file_search_service.py
│   │   │   ├── ocr/
|   |   |   |   ├── ocr_service.py
│   │   │   ├── pipelines/
|   |   |   |   ├── embedding_pipeline.py
|   |   |   |   ├── enrichment_pipeline.py
|   |   |   |   ├── retrieval_pipeline.py 
│   │   │   ├── tagging/
|   |   |   |   ├── auto_tagging_service.py
|   |   |   |   ├── image_tagging_service.py
|   |   |   |   ├── pdf_tagging_service.py 
|   |   |   |   ├── tag_cleaner_service.py
|   |   |   |   ├── video_tagging_Service.py
│   │   │   └── retrieval/
|   |   |   |   ├── hybrid_search_Service.py
|   |   |   |   ├── keyword_search_service.py
|   |   |   |   ├── semantic_search_service.py
│   │   │
│   │   ├── workers/
│   │   │   ├── queues/
│   │   │   ├── processors/
│   │   │   └── schedulers/
│   │   │
│   │   ├── repositories/
│   │   │
│   │   ├── db/
│   │   │   ├── seed/
│   │   │   └── session/
│   │   ├── main.py
│   │   └── utils/
│   │
│   ├── tests/
│   │
│   └── requirements.txt
│
├── infrastructure/
│   ├── docker/
│   ├── kubernetes/
│   ├── terraform/
│   └── monitoring/
│
├── datasets/
│   ├── sample_assets/
│   ├── taxonomy/
│   └── metadata_templates/
│
├── notebooks/
│   ├── experimentation/
│   ├── embedding_tests/
│   ├── tagging_tests/
│   └── retrieval_evaluation/
│
├── docs/
│   ├── architecture/
│   ├── api_specs/
│   ├── workflows/
│   └── ai_design/
│
├── storage/
│   ├── originals/
│   ├── thumbnails/
│   ├── previews/
│   ├── archived/
│   └── temp/
└── README.md