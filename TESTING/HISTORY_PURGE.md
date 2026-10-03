# Git History Purge Protocol (Burned Competition Labels)

> [!WARNING]
> Because early development commits contained `datasets/sample_hidden_test.csv` and matching predictions, those initial sample labels must be considered **burned**. Before launching the live competition, competition organizers must generate fresh private test labels and purge historical commits from the repository history.

---

## 1. Prerequisites
Ensure you have a complete clone and a backup before rewriting git history:

```bash
# Clone a fresh mirror of the repository
git clone --mirror https://github.com/chakravyuha-club/Agent_Eval.git agent_eval_backup.git
cd agent_eval_backup.git
```

Install `git-filter-repo` (recommended by Git):
```bash
pip install git-filter-repo
```
Or download [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/).

---

## 2. Option A: Using `git-filter-repo` (Recommended)

Run the following command to completely remove the legacy sample dataset files from all branches, tags, and commits:

```bash
# Analyze repository
git filter-repo --analyze

# Purge specific files from entire commit history
git filter-repo --path datasets/sample_hidden_test.csv --invert-paths
git filter-repo --path datasets/sample_submission.csv --invert-paths

# Force push the rewritten history to the remote repository
git remote add origin https://github.com/chakravyuha-club/Agent_Eval.git
git push origin --force --all
git push origin --force --tags
```

---

## 3. Option B: Using BFG Repo-Cleaner

```bash
# Remove files with BFG
java -jar bfg.jar --delete-files sample_hidden_test.csv
java -jar bfg.jar --delete-files sample_submission.csv

# Expire old reflogs and garbage-collect
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push clean history
git push origin --force --all
git push origin --force --tags
```

---

## 4. Post-Purge Verification

1. Verify that no commit contains the purged files:
   ```bash
   git log --all --full-history -- "**/sample_hidden_test.csv"
   ```
   *(This should return zero commits)*.

2. Verify that local repository references are clean and teammates re-clone:
   ```bash
   git clone https://github.com/chakravyuha-club/Agent_Eval.git
   ```

3. Ensure production environment points to fresh private files:
   ```bash
   export GROUND_TRUTH_PATH="/etc/agentscore/secrets/stage1_ground_truth_2026.csv"
   export STAGE2_SUITE_PATH="/etc/agentscore/secrets/stage2_suite_2026.json"
   ```
