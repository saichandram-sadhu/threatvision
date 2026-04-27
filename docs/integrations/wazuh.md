# Wazuh → ThreatVision webhooks

Wazuh can forward alerts as JSON to ThreatVision’s **generic SIEM webhook** endpoint. Use the same auth modes and body shape as the main SIEM guide.

## Quick setup

1. In ThreatVision, provision a webhook secret (per-user) so you obtain a **`path_key`** (and optional HMAC secret if you enable it).
2. In Wazuh (e.g. **Integrations** / custom output), POST JSON to:

   - `POST https://<your-threatvision-api-host>/api/webhook/siem/<path_key>`

   or use the header variant documented in [siem-webhooks.md](./siem-webhooks.md).

3. Map alert fields to IOCs using **`_threatvision.iocPaths`** in the JSON body when the extractor cannot infer fields automatically (see SIEM guide).

## References

- Full schema, HMAC, and examples: [siem-webhooks.md](./siem-webhooks.md)
- Wazuh integration patterns depend on your version (manager `ossec.conf`, rules, or indexer pipelines); point your HTTP output at the URL above and ensure TLS and secrets are handled per your security policy.
