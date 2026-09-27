# Set up Cloudflare audio hosting

The default setup asks for an account ID and one short-lived setup token. The CLI creates a private bucket in the default jurisdiction and saves a separate upload key restricted to that bucket. Existing R2 credentials are reused. Local-only audio needs no Cloudflare account.

## Create the setup token

Show these instructions before asking for the secret. The user completes the Cloudflare dashboard steps themselves; never ask them to paste a token in chat.

1. Open the [Cloudflare dashboard](https://dash.cloudflare.com/), select the account that will store the audio, and open **Storage & databases > R2 Object Storage > Overview**. Activate R2 if necessary. Cloudflare may require billing details; the Bot cannot accept billing terms for the user.
2. Copy the **Account ID** from the R2 overview's **Account Details**. It is a 32-character ID, not an email address, bucket name, or zone ID.
3. Open **Manage Account > Account API Tokens > Create Token**. Use a custom token if a template picker appears. Name it **Article Audio setup**. Creating account-owned tokens requires **Super Administrator** access. If this page or the permissions below are unavailable, use the manual fallback.
4. Add these two permission rows, both at **Account** scope:
   - **Workers R2 Storage > Edit**. The API calls this `Workers R2 Storage Write`. It permits bucket administration and object access across the selected account's R2 storage.
   - **Account API Tokens > Edit**. The API calls this `Account API Tokens Write`. It lets setup create the separate bucket-restricted upload token. This is account token-management authority, broader than access to one bucket.
5. Limit resources to **this account only**. Where shown, choose **Include > Specific account > your account**. Do not grant all accounts, zone permissions, or use a Global API Key. Set an expiration within **one day**, long enough to finish setup. Avoid an IP restriction unless you know the Bot computer's stable outbound IP, since it is not your laptop's IP.
6. Choose **Continue to summary**, review the permissions and expiry, then **Create Token**. Cloudflare shows the token value once. Enter it through Grok's native secure secret card as `CLOUDFLARE_API_TOKEN`; supply the account ID as `CLOUDFLARE_ACCOUNT_ID`. If native handoff cannot deliver values to the CLI, use the two-field local form below.

[Account-token dashboard instructions](https://developers.cloudflare.com/fundamentals/api/get-started/account-owned-tokens/), [initial token permissions](https://developers.cloudflare.com/fundamentals/api/how-to/create-via-api/), and [bucket API permission](https://developers.cloudflare.com/api/resources/r2/subresources/buckets/methods/create/) document these requirements.

## Run automatic setup

With a supported native handoff, inject the two names above into the process environment and run `auth provision-r2`. There is no need to copy the setup token into a file first. If the host only supports secure JSON on stdin, use `auth import-json` first. Never interpolate secrets into commands or inspect filled fields.

Otherwise, keep the local setup process alive and let the user enter both values in the Agent Computer browser:

```bash
bash scripts/article-audio auth setup cloudflare
bash scripts/article-audio auth provision-r2
```

The second command creates a new `article-audio-<random suffix>` bucket, checks that r2.dev and custom-domain access are disabled, resolves the bucket object-write permission, and creates a token scoped only to that bucket. It derives the S3 credentials as documented by [Cloudflare](https://developers.cloudflare.com/r2/api/tokens/) and saves all four R2 fields without returning their values. It never enables public access or changes another bucket's settings.

The CLI removes the matching setup token from its credential file after saving the upload key. If another process saved replacement Cloudflare credentials during setup, it preserves them and reports `setup_token_removed_from_file:false`. Follow the returned cleanup guidance, revoking only the token used for this run and leaving replacement credentials intact. **This does not revoke the token at Cloudflare or remove a native Grok secret/environment entry.** Generate the original sample, publish it, and return its verified listening link. Then guide the user to revoke **Article Audio setup** on the Account API Tokens page and remove its saved Grok secret/environment entry. Keep the new `article-audio-<suffix>-uploads` token. Renew the sample link with `publish` after cleanup to confirm ongoing access. Never declare hosted setup complete from credential presence or bucket creation alone.

`auth provision-r2` reuses complete R2 credentials without creating resources. It refuses partial existing R2 configuration, so finish that configuration with the manual form. Automatic setup creates an ordinary `default`-jurisdiction bucket; use the manual path for `eu`, `us`, or `fedramp` requirements. Save the jurisdiction in the Bot's nonsecret configuration and pass it on every publish.

## Manual fallback: existing four-field form

Offer this immediately if the user already has a bucket, lacks token-management permissions, wants a jurisdictional bucket, or prefers not to grant setup authority. Do not keep pushing the automatic path after they choose manual setup.

1. In **R2 Object Storage > Overview**, create or select a private bucket. Keep public r2.dev and custom-domain access disabled for private listening links.
2. In the R2 overview, find **Account Details > API Tokens > Manage**. Create an R2 account token, or a user token if permitted by the account. Select **Object Read & Write**, then **Apply to specific buckets only**, selecting this bucket.
3. Copy the S3 **Access Key ID** and **Secret Access Key** from the confirmation. The API token value is not the Secret Access Key.
4. Use native secure cards for missing values when supported, or open the unchanged four-field form with `auth setup r2`. It asks for `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, and `R2_BUCKET`.
5. Publish the sample and verify the returned link. If upload fails, retain the MP3 and repair hosting without regenerating audio.

## Failed or interrupted setup

Denied requests require checking the exact account, both permissions, token expiry, R2 activation, and role. Do not print Cloudflare responses or secret values. Fall back to manual setup if the user cannot grant the required access.

Setup reserves its bucket name in private `r2-setup.json` before creating resources. Retrying can reuse that bucket. A token-create request can succeed remotely even if the connection drops before the secret is saved. In this case a normal retry stops with the exact token name to inspect. Revoke any token with that name in Cloudflare, then run `auth provision-r2 --retry-token`. Use that flag only after the user confirms revocation, or authorized account inspection proves no such token exists. Never blindly retry, delete the bucket, or delete the setup record to bypass recovery. The manual form is also available; revoke any orphan upload token when choosing it.

The setup record stores account, bucket name, and request state, never a token. Preserve it outside exports. A damaged record requires account reconciliation or manual setup, not automatic deletion. Existing recordings and Gemini credentials are preserved.

## Optional Cloudflare plugin

The [Cloudflare plugin](https://cursor.com/marketplace/cloudflare) may help with documentation or account operations when Grok exposes its authenticated tools. This package's automatic setup uses the Cloudflare API directly and needs no plugin. A plugin login does not automatically supply S3 credentials. Never extract its private OAuth token or claim that installation alone configured hosting.
