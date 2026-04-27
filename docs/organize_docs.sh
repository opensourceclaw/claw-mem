#!/bin/bash
# claw-mem 文档分类脚本

cd /Users/liantian/workspace/osprojects/claw-mem/docs

# v1.0.0 相关文档
mv CLAW_MEM_V1.0.0_DOCUMENTATION.md v1.0.0/ 2>/dev/null || true
mv BUSINESS_AGENT_REPORT_v100.md v1.0.0/ 2>/dev/null || true
mv COMMERCIALIZATION_PLAN_v1.0.md v1.0.0/ 2>/dev/null || true
mv GITHUB_RELEASE_NOTES_v100.md v1.0.0/ 2>/dev/null || true
mv RELEASE_NOTES_v100.md v1.0.0/ 2>/dev/null || true

# v1.0.1 相关文档
mv RELEASE_NOTES_v101.md v1.0.1/ 2>/dev/null || true
mv DEPLOYMENT_V101.md v1.0.1/ 2>/dev/null || true

# v1.0.2 相关文档
mv ITERATION_PLAN_v1.0.2.md v1.0.2/ 2>/dev/null || true
mv MEMORY_SCHEMA_v1.0.2.md v1.0.2/ 2>/dev/null || true

# v1.0.3 相关文档
mv ITERATION_PLAN_v1.0.3.md v1.0.3/ 2>/dev/null || true

# v1.0.4 相关文档
mv ITERATION_PLAN_v1.0.4.md v1.0.4/ 2>/dev/null || true

# v1.0.5 相关文档
mv DEPLOYMENT_REPORT_v1.0.5.md v1.0.5/ 2>/dev/null || true

# v1.0.6, v1.0.7, v1.0.8 暂无特定文档，保留目录

# 归档旧版本文档
mv RELEASE_v060.md archive/ 2>/dev/null || true
mv RELEASE_v070.md archive/ 2>/dev/null || true
mv RELEASE_REPORT_v070.md archive/ 2>/dev/null || true
mv RELEASE_PLAN_v070.md archive/ 2>/dev/null || true
mv RELEASE_NOTES_v070.md archive/ 2>/dev/null || true
mv FEATURES_v080.md archive/ 2>/dev/null || true
mv RELEASE_PLAN_v080.md archive/ 2>/dev/null || true
mv RELEASE_NOTES_v080.md archive/ 2>/dev/null || true
mv RELEASE_SUMMARY_v080.md archive/ 2>/dev/null || true
mv RELEASE_CHECKLIST_v080.md archive/ 2>/dev/null || true
mv FINAL_RELEASE_REPORT_v080.md archive/ 2>/dev/null || true
mv REQUIREMENTS_v080.md archive/ 2>/dev/null || true
mv CODE_REVIEW_v090.md archive/ 2>/dev/null || true
mv COMPARISON_v080_vs_v090.md archive/ 2>/dev/null || true
mv ERROR_CODES_v090.md archive/ 2>/dev/null || true
mv PRE_RELEASE_REVIEW_v090.md archive/ 2>/dev/null || true
mv RELEASE_PLAN_v090.md archive/ 2>/dev/null || true
mv RELEASE_PLAN_v090_FINAL.md archive/ 2>/dev/null || true
mv RELEASE_NOTES_v090_DRAFT.md archive/ 2>/dev/null || true
mv RELEASE_CHECKLIST_v090.md archive/ 2>/dev/null || true
mv RELEASE_COMPLETE_v090.md archive/ 2>/dev/null || true
mv GITHUB_RELEASE_NOTES_v090.md archive/ 2>/dev/null || true

# 归档其他旧文档
mv F000_MEMORY_FIX_PLAN.md archive/ 2>/dev/null || true
mv F1_IMPLEMENTATION.md archive/ 2>/dev/null || true
mv F2_LAZY_LOADING.md archive/ 2>/dev/null || true
mv F5_COMPRESSION.md archive/ 2>/dev/null || true
mv F6_RECOVERY.md archive/ 2>/dev/null || true
mv F7_PERFORMANCE_TEST.md archive/ 2>/dev/null || true

# research 目录已存在，保留原有内容

echo "claw-mem 文档分类完成！"
