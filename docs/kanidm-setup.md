# Kanidm Setup Guide for FiberQ

This guide covers configuring [Kanidm](https://kanidm.com/) as the identity provider for the FiberQ WebUI and API.

## Prerequisites

- Kanidm server running and accessible (e.g., `https://idm.example.com`)
- Admin CLI access (`kanidm` binary configured to talk to the server)
- TLS certificate trusted by all services that will connect to Kanidm

## 1. Authenticate as Admin

```bash
kanidm login --name admin
```

If running inside the Kanidm container, configure the CLI first:

```bash
mkdir -p ~/.config/kanidm
echo 'uri = "https://localhost:8443"' > ~/.config/kanidm/config.toml
```

## 2. Create the OAuth2 Client

```bash
kanidm system oauth2 create fiberq "FiberQ WebUI" https://your-domain.example.com
```

## 3. Configure Redirect URIs

Add callback URLs for both development and production:

```bash
# Development
kanidm system oauth2 add-redirect-url fiberq http://localhost:3000/api/auth/callback/kanidm

# Production
kanidm system oauth2 add-redirect-url fiberq https://your-domain.example.com/api/auth/callback/kanidm
```

## 4. Create Role Groups

FiberQ uses Kanidm groups with a `fiberq_` prefix to determine user roles.
The prefix is stripped at runtime (e.g., `fiberq_admin` becomes role `admin`).

```bash
kanidm group create fiberq_admin --name idm_admin
kanidm group create fiberq_project_manager --name idm_admin
kanidm group create fiberq_engineer --name idm_admin
kanidm group create fiberq_field_worker --name idm_admin
```

### Role Permissions

| Group                    | Role              | Access                                    |
|--------------------------|-------------------|-------------------------------------------|
| `fiberq_admin`           | `admin`           | Full access, user management, all projects |
| `fiberq_project_manager` | `project_manager` | Project CRUD, user assignment              |
| `fiberq_engineer`        | `engineer`        | Project data, sync, fiber planning         |
| `fiberq_field_worker`    | `field_worker`    | Assigned projects only, field data entry   |

## 5. Configure Scope Maps

Scope maps control which groups can authenticate and what claims they receive.
Every group that should be able to log in needs a scope map with at least `openid`.

```bash
kanidm system oauth2 update-scope-map fiberq fiberq_admin openid profile email groups
kanidm system oauth2 update-scope-map fiberq fiberq_project_manager openid profile email groups
kanidm system oauth2 update-scope-map fiberq fiberq_engineer openid profile email groups
kanidm system oauth2 update-scope-map fiberq fiberq_field_worker openid profile email groups
```

**Important:** The `groups` scope is required for FiberQ to read role membership from the token.

## 6. Assign Users to Groups

```bash
# Add a user to the admin role
kanidm group add-members fiberq_admin <username> --name idm_admin

# Add a user to the field worker role
kanidm group add-members fiberq_field_worker <username> --name idm_admin
```

A user can belong to multiple role groups. The application grants the union of all role permissions.

## 7. Retrieve the Client Secret

```bash
kanidm system oauth2 show-basic-secret fiberq
```

Save this value -- you'll need it for the WebUI environment configuration.

## 8. Optional: Display Settings

Use short usernames instead of SPNs (e.g., `rosen` instead of `rosen@idm.example.com`):

```bash
kanidm system oauth2 prefer-short-username fiberq
```

## 9. Configure FiberQ Environment

### WebUI (`web/.env.local`)

```env
AUTH_KANIDM_ID=fiberq
AUTH_KANIDM_SECRET=<secret from step 7>
KANIDM_URL=https://idm.example.com
AUTH_SECRET=<generate with: openssl rand -base64 32>
AUTH_TRUST_HOST=true
NEXTAUTH_URL=http://localhost:3000
```

### API Server (`server/.env`)

```env
KANIDM_URL=https://idm.example.com
KANIDM_CLIENT_ID=fiberq
KANIDM_VERIFY_TLS=true
```

Set `KANIDM_VERIFY_TLS=false` only if using self-signed certificates in development.

## 10. Verify the Setup

```bash
# Check the OAuth2 client configuration
kanidm system oauth2 get fiberq

# Check the OIDC discovery endpoint responds
curl -s https://idm.example.com/oauth2/openid/fiberq/.well-known/openid-configuration | python3 -m json.tool
```

Expected: JSON with `authorization_endpoint`, `token_endpoint`, `userinfo_endpoint`, `jwks_uri`.

## Technical Details

### Token Format

- **Algorithm:** ES256 (ECDSA with P-256 and SHA-256) by default
- **Format:** RFC 9068 JWT
- **Groups claim:** Array of group names the user belongs to (when `groups` scope is granted)

### OIDC Endpoints

| Endpoint       | URL                                                                 |
|----------------|---------------------------------------------------------------------|
| Discovery      | `{KANIDM_URL}/oauth2/openid/fiberq/.well-known/openid-configuration` |
| Authorization  | `{KANIDM_URL}/ui/oauth2`                                            |
| Token          | `{KANIDM_URL}/oauth2/token`                                         |
| UserInfo       | `{KANIDM_URL}/oauth2/openid/fiberq/userinfo`                        |
| JWKS           | `{KANIDM_URL}/oauth2/openid/fiberq/public_key.jwk`                  |

### Role Extraction Flow

```
Kanidm groups  -->  "groups" claim in JWT  -->  filter fiberq_ prefix  -->  strip prefix  -->  app roles
fiberq_admin        ["fiberq_admin", ...]       ["fiberq_admin"]            ["admin"]           admin
```

## Troubleshooting

### "Name or service not known" inside container

The Kanidm CLI inside the container can't resolve external DNS. Use `https://localhost:8443` in the CLI config when running commands from within the Kanidm container.

### Token validation fails with "unsupported algorithm"

Kanidm uses ES256 by default. If your downstream service only supports RS256, enable legacy crypto:

```bash
kanidm system oauth2 warning-enable-legacy-crypto fiberq
```

### User can't log in

Verify the user belongs to at least one group that has a scope map for this client:

```bash
kanidm person get <username> --name idm_admin
kanidm system oauth2 get fiberq
```

### Redirect URI mismatch

Ensure the callback URL exactly matches what Auth.js sends. The format is:
`{NEXTAUTH_URL}/api/auth/callback/kanidm`
