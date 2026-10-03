# AgentScore Datasets

## Security & Storage Architecture

1. **Public Datasets**:
   - `training_dataset.csv`: Historical training examples with ground truth labels.
   - `public_test_features.csv`: Benchmark tasks for offline agent prototyping.
   - `sample_submission.csv`: Formatting reference for Stage 1 tabular submissions.
   - `sample_stage2_suite.json`: Developer mock suite for testing agent HTTP endpoints (`/health` and `/predict`).

2. **Private Ground Truth (Crucial Security Rule)**:
   - **NEVER** commit competition ground truth labels or final Stage 2 task suites to this git repository.
   - In production, set the environment variables:
     - `GROUND_TRUTH_PATH=/secure/private_storage/official_stage1_hidden_labels.csv`
     - `STAGE2_SUITE_PATH=/secure/private_storage/official_stage2_suite.json`
   - Files in `datasets/sample_hidden_test.csv` are **DEVELOPMENT MOCK SAMPLES ONLY**. The backend strictly requires external private storage paths in production mode (`ENVIRONMENT=production`).

3. **Label Leak Prevention Policy**:
   - Platform CI blocks pull requests that attempt to commit files with naming patterns `*private*` or `*secret*`.
   - Participants only receive aggregated failure category counts and total benchmark scores—per-task pass/fail feedback on hidden tasks is strictly restricted to platform administrators to eliminate score oracle recovery attacks.
