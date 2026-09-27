# Cloudflare setup and the optional plugin

For hosted listening, configure Gemini and R2 during the initial Bot setup, then publish the original sample to a private bucket and return its verified playback link. A local-only setup can skip R2.

The uploader needs four values: `R2_ACCOUNT_ID`, `R2_BUCKET`, `R2_ACCESS_KEY_ID`, and `R2_SECRET_ACCESS_KEY`. The last two come from an R2 token with **Object Read & Write** permissions scoped to the selected bucket. A generic Cloudflare API token is not the same credential pair. Use `auth setup r2` or the supported native secure handoff. Save and reuse the values outside the source repository.

## Optional help from the Cloudflare plugin

The [Cursor Marketplace listing](https://cursor.com/marketplace/cloudflare) includes skills and authenticated MCP tools. Its linked version bundles the documentation, Bindings, Builds, and Observability servers. The [Bindings server](https://github.com/cloudflare/mcp-server-cloudflare/blob/main/apps/workers-bindings/README.md) supports listing, inspecting, creating, and deleting R2 buckets after Cloudflare OAuth authorization. It can help find or provision the bucket if Grok exposes those tools and the user authorizes the action.

The [current upstream plugin](https://github.com/cloudflare/skills) instead bundles Cloudflare's general Code Mode server. Installed capabilities depend on the distributed version, host support, and granted account permissions. Inspect available tools before promising provisioning. Installing a plugin alone does not grant account access.

Neither the marketplace's listed bucket tools nor this package implement an OAuth-to-S3 credential handoff. The CLI uses boto3's S3 API, so keep collecting the bucket-scoped Access Key ID and Secret Access Key unless the installed host provides a verified secure way to provision and inject them. Do not extract a plugin's private OAuth token or claim that its login configured this uploader.

## Guided setup

1. Select an existing private bucket, or create one with authorized plugin tools or the Cloudflare dashboard. R2 must be enabled on the account. Do not enable public access for the default signed-link flow.
2. In **R2 Object Storage → Manage API Tokens**, create a token with **Object Read & Write** access scoped to that bucket. Enter the Access Key ID and Secret Access Key directly in the secure handoff or local form. Cloudflare only shows the secret at creation time.
3. Supply the account ID and bucket name in the same form. `auth status` confirms presence; it does not prove access.
4. Generate the original sample and run `publish` on its returned MP3 path. Only a successful upload and playback-range check verifies hosting. If it fails, retain the MP3 and repair credentials or configuration without regenerating audio.

For buckets in a jurisdiction, add `--jurisdiction eu`, `--jurisdiction us`, or `--jurisdiction fedramp` when publishing, or set `R2_JURISDICTION` consistently in the Bot environment. The default is `default`. This selects Cloudflare's required jurisdiction-specific S3 hostname; it is separate from a bucket's location hint. Keep the selected value in the Bot's nonsecret configuration so later uploads use the same endpoint.

[Cloudflare's authentication and permission documentation](https://developers.cloudflare.com/r2/api/tokens/) is the source of truth for token setup.
