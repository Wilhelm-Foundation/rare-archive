# Rare AI Archive — User Management

## OpenWebUI Instance

- **URL**: `https://latlab-dell:3100` (via Tailscale) or `http://localhost:3100` (SSH tunnel)
- **Version**: 0.8.10
- **Container**: `rare-archive-openwebui`

## User Accounts

| Email | Name | Role | Password |
|-------|------|------|----------|
| `science.stanley@stanley.science` | Stanley | admin | (standard alpha password) |
| `herb@lattice.bio` | Herb | admin | (standard alpha password) |
| `jaco@lattice.bio` | Jaco | user | (standard alpha password) |
| `eric@lattice.bio` | Eric | user | (standard alpha password) |
| `sat@lattice.bio` | Sat | user | (standard alpha password) |
| `henk@lattice.bio` | Henk | user | (standard alpha password) |
| `demo@wilhelm.foundation` | Demo User | user | `RareAI2026!` |
| `clinician@wilhelm.foundation` | Clinician Demo | user | `RareAI2026!` |

## Creating New Users

Users are created via the admin API (signup is disabled):

```bash
# Get admin JWT
TOKEN=$(curl -s http://localhost:3100/api/v1/auths/signin \
  -H "Content-Type: application/json" \
  -d '{"email": "ADMIN_EMAIL", "password": "ADMIN_PASSWORD"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Create user
curl -s http://localhost:3100/api/v1/auths/add \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "name": "User Name", "password": "password", "role": "user"}'
```

Valid roles: `admin`, `user`, `pending`.

## Model Visibility

By default, external models (from llama-server backends) are **Private** — only admins can see them. To make models accessible to all users:

1. Admin Panel → Settings → Models
2. Click the edit (pencil) icon on each model
3. Click "Access" button → change from "Private" to "Public"
4. Repeat for workspace models (Workspace → Models → Edit → Access)

Currently configured as Public:
- `qwen3.5-35b-a3b-q8_0.gguf` (Primary — Qwen 3.5 35B-A3B)
- `rare-archive-qwen-4b-sft-v1-Q8_0.gguf` (Fine-tuned 4B SFT)
- `rare-disease-specialist` (Preset wrapping 35B with system prompt + 7 tools)
- `arena-model` (Arena mode — admin-visible only)

## Password Reset (Direct SQLite)

When the admin API is inaccessible (e.g., all admin passwords stale), reset passwords via direct SQLite manipulation:

```bash
# 1. Generate bcrypt hash
HASH=$(docker exec rare-archive-openwebui python3 -c \
  "import bcrypt; print(bcrypt.hashpw(b'NEW_PASSWORD', bcrypt.gensalt()).decode())")

# 2. Update password in SQLite
docker exec rare-archive-openwebui sqlite3 /app/backend/data/webui.db \
  "UPDATE auth SET password='$HASH' WHERE email='user@example.com';"

# 3. CRITICAL: Restart container — ORM caches prevent seeing direct writes
docker restart rare-archive-openwebui

# 4. Verify login
curl -s http://localhost:3100/api/v1/auths/signin \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "NEW_PASSWORD"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'token' in d else 'FAIL')"
```

**Important**: The container restart in step 3 is mandatory. OpenWebUI uses SQLAlchemy ORM which caches model instances — direct SQLite changes are invisible until the process restarts.

**Bulk reset** (all accounts to same password):

```bash
HASH=$(docker exec rare-archive-openwebui python3 -c \
  "import bcrypt; print(bcrypt.hashpw(b'NEW_PASSWORD', bcrypt.gensalt()).decode())")
docker exec rare-archive-openwebui sqlite3 /app/backend/data/webui.db \
  "UPDATE auth SET password='$HASH';"
docker restart rare-archive-openwebui
```

## Environment Variables

Key auth-related env vars in `docker-compose.rare-archive.yaml`:

```yaml
ENABLE_SIGNUP: false        # No self-registration
WEBUI_AUTH: true             # Authentication required
ENABLE_ARENA_MODEL: true    # Arena comparison mode enabled
```
