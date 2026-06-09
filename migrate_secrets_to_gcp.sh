#!/usr/bin/env bash
# =============================================================================
# Migrate API keys from .env → Google Cloud Secret Manager
# =============================================================================
# Run AFTER setup_gcp.sh. This script uploads each secret to Secret Manager
# so you can stop storing credentials in .env / source control.
#
# Usage:
#   chmod +x migrate_secrets_to_gcp.sh
#   ./migrate_secrets_to_gcp.sh
# =============================================================================
set -euo pipefail

GCLOUD="/opt/homebrew/Caskroom/gcloud-cli/571.0.0/google-cloud-sdk/bin/gcloud"
ENV_FILE="$(pwd)/.env"

ok()   { printf '  \033[32m✓\033[0m  %s\n' "$*"; }
warn() { printf '  \033[33m⚠\033[0m  %s\n' "$*"; }
info() { printf '  \033[34mℹ\033[0m  %s\n' "$*"; }

PROJECT_ID="$("$GCLOUD" config get-value project 2>/dev/null)"
[[ -n "$PROJECT_ID" ]] || { echo "Run setup_gcp.sh first to set the active project."; exit 1; }

# Secrets to migrate. Secret Manager names match config.py's default mapping:
#   OPENAI_API_KEY -> openai-api-key
SECRETS=(
  OPENAI_API_KEY
  TAVILY_API_KEY
  SERPER_API_KEY
  GHOST_ADMIN_KEY
  GHOST_CONTENT_API_KEY
)

echo ""
echo "Migrating secrets to Secret Manager (project: $PROJECT_ID)"
echo ""

for env_var in "${SECRETS[@]}"; do
  secret_name="$(echo "$env_var" | tr '[:upper:]_' '[:lower:]-')"
  value="$(grep "^${env_var}=" "$ENV_FILE" 2>/dev/null | cut -d= -f2- || true)"

  if [[ -z "$value" ]]; then
    warn "$env_var not found in .env — skipping"
    continue
  fi

  # Create secret if it doesn't exist
  if ! "$GCLOUD" secrets describe "$secret_name" --project="$PROJECT_ID" &>/dev/null; then
    "$GCLOUD" secrets create "$secret_name" \
      --replication-policy="automatic" \
      --project="$PROJECT_ID"
  fi

  # Add a new version with the current value
  echo -n "$value" | "$GCLOUD" secrets versions add "$secret_name" \
    --data-file=- \
    --project="$PROJECT_ID"

  ok "$env_var → projects/$PROJECT_ID/secrets/$secret_name"
done

echo ""
echo "Done! To use Secret Manager in your app, set USE_SECRET_MANAGER=true in .env"
echo "The app will then fetch secrets from GCP instead of reading .env values."
echo ""
