#!/usr/bin/env bash
# =============================================================================
# Google Cloud Platform — Project Setup for automated_blog_platform
# =============================================================================
# Run once to authenticate, create a service account, provision a GCS bucket,
# enable APIs, and populate .env with the resulting values.
#
# Usage:
#   chmod +x setup_gcp.sh
#   ./setup_gcp.sh
# =============================================================================
set -euo pipefail

GCLOUD="${GCLOUD:-gcloud}"
GSUTIL="${GSUTIL:-gsutil}"
# ── Configurable ─────────────────────────────────────────────────────────────
# Replace with your actual GCP project ID (find it in Cloud Console → home)
PROJECT_ID="${GCP_PROJECT_ID:-auto-blog-platform}"
REGION="${GCP_REGION:-us-central1}"
SA_NAME="auto-blog-sa"
SA_DISPLAY="Auto Blog Platform Service Account"
KEY_FILE="$(pwd)/credentials/gcp-service-account.json"
BUCKET_NAME="${PROJECT_ID}-media"
# ─────────────────────────────────────────────────────────────────────────────

bold()  { printf '\033[1m%s\033[0m\n' "$*"; }
info()  { printf '  \033[34mℹ\033[0m  %s\n' "$*"; }
ok()    { printf '  \033[32m✓\033[0m  %s\n' "$*"; }
warn()  { printf '  \033[33m⚠\033[0m  %s\n' "$*"; }
die()   { printf '  \033[31m✗\033[0m  %s\n' "$*" >&2; exit 1; }

bold "═══════════════════════════════════════════════════"
bold "  GCP Setup — automated_blog_platform"
bold "═══════════════════════════════════════════════════"
echo ""

# ── 0. Sanity-check gcloud ────────────────────────────────────────────────────
[[ -x "$GCLOUD" ]] || die "gcloud not found at $GCLOUD. Re-run after brew install google-cloud-sdk."

# ── 1. Authenticate ───────────────────────────────────────────────────────────
bold "Step 1/7 — Authenticate"
info "Opening browser for Google account login…"
"$GCLOUD" auth login --quiet

info "Setting up Application Default Credentials (used by SDK + libraries)…"
"$GCLOUD" auth application-default login --quiet
ok "Authenticated"

# ── 2. Set project ────────────────────────────────────────────────────────────
bold "Step 2/7 — Set active project"
"$GCLOUD" config set project "$PROJECT_ID"
ok "Active project: $PROJECT_ID"

# ── 3. Enable required APIs ───────────────────────────────────────────────────
bold "Step 3/7 — Enable GCP APIs"
APIS=(
  storage.googleapis.com           # Cloud Storage  
  secretmanager.googleapis.com     # Secret Manager
  iam.googleapis.com               # IAM
  run.googleapis.com               # Cloud Run (for future deployment)
  sqladmin.googleapis.com          # Cloud SQL (for future DB migration)
  logging.googleapis.com           # Cloud Logging
  cloudscheduler.googleapis.com    # Cloud Scheduler (automate pipeline runs)
)
for api in "${APIS[@]}"; do
  info "Enabling $api"
  "$GCLOUD" services enable "$api" --project="$PROJECT_ID" --quiet
done
ok "All APIs enabled"

# ── 4. Create service account ────────────────────────────────────────────────
bold "Step 4/7 — Service account"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if "$GCLOUD" iam service-accounts describe "$SA_EMAIL" --project="$PROJECT_ID" &>/dev/null; then
  warn "Service account $SA_EMAIL already exists — skipping creation"
else
  "$GCLOUD" iam service-accounts create "$SA_NAME" \
    --display-name="$SA_DISPLAY" \
    --project="$PROJECT_ID"
  ok "Service account created: $SA_EMAIL"
  info "Waiting for service account to propagate..."
  sleep 15
fi

# Grant roles
ROLES=(
  roles/storage.admin              # Read/write GCS buckets
  roles/secretmanager.secretAccessor  # Read secrets
  roles/logging.logWriter          # Write logs
  roles/cloudscheduler.jobRunner   # Trigger scheduled jobs
)
for role in "${ROLES[@]}"; do
  info "Granting $role"
  "$GCLOUD" projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="$role" \
    --quiet
done
ok "Roles granted"

# ── 5. Download service-account key ──────────────────────────────────────────
bold "Step 5/7 — Service account key"
mkdir -p "$(dirname "$KEY_FILE")"
if [[ -f "$KEY_FILE" ]]; then
  warn "Key file already exists at $KEY_FILE — skipping download"
else
  "$GCLOUD" iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SA_EMAIL" \
    --project="$PROJECT_ID"
  ok "Key saved to $KEY_FILE"
fi

# ── 6. Create GCS media bucket ───────────────────────────────────────────────
bold "Step 6/7 — GCS bucket"
if "$GSUTIL" ls -b "gs://${BUCKET_NAME}" &>/dev/null; then
  warn "Bucket gs://$BUCKET_NAME already exists — skipping"
else
  "$GSUTIL" mb -p "$PROJECT_ID" -l "$REGION" "gs://${BUCKET_NAME}"
  # Allow public reads so uploaded media is accessible via public URL
  "$GSUTIL" iam ch allUsers:objectViewer "gs://${BUCKET_NAME}"
  ok "Bucket created: gs://$BUCKET_NAME"
fi

# ── 7. Patch .env ─────────────────────────────────────────────────────────────
bold "Step 7/7 — Update .env"
ENV_FILE="$(pwd)/.env"

patch_env() {
  local key="$1" val="$2"
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    # Replace existing line
    sed -i.bak "s|^${key}=.*|${key}=${val}|" "$ENV_FILE"
  else
    echo "${key}=${val}" >> "$ENV_FILE"
  fi
}

patch_env "GCP_PROJECT_ID"                "$PROJECT_ID"
patch_env "GCS_BUCKET_NAME"              "$BUCKET_NAME"
patch_env "GOOGLE_APPLICATION_CREDENTIALS" "$KEY_FILE"
patch_env "GCP_REGION"                   "$REGION"
patch_env "GCP_SA_EMAIL"                 "$SA_EMAIL"

# Clean up backup created by sed
rm -f "${ENV_FILE}.bak"

ok ".env updated"

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
bold "═══════════════════════════════════════════════════"
bold "  ✅  GCP setup complete!"
bold "═══════════════════════════════════════════════════"
echo ""
echo "  Project  : $PROJECT_ID"
echo "  Bucket   : gs://$BUCKET_NAME"
echo "  SA email : $SA_EMAIL"
echo "  Key file : $KEY_FILE"
echo ""
echo "  Next steps:"
echo "  1. Run: source ~/.zshrc  (or open a new terminal)"
echo "  2. Optionally run: ./migrate_secrets_to_gcp.sh"
echo "     to move API keys from .env → Secret Manager"
echo ""
