# Future SIEM/SOAR/EDR Integration

O.R.A.C.L.E Framework does not implement SIEM, SOAR, or EDR connectors in the current release. These integrations are documented as optional future extensions so they can be added without bypassing Oracle Core, EthicQ, ChronoLedger, or promotion-safety controls.

## A. SIEM Integration

Recommended first targets:

- Wazuh
- Elastic / ELK
- Splunk
- Microsoft Sentinel

Recommended integration methods:

- JSON alert forwarding
- Syslog output
- Webhook output
- Filebeat/log shipping
- REST API export

Example ORACLE alert JSON:

```json
{
  "oracle_trace_id": "...",
  "risk_score": 0.92,
  "risk_label": "HIGH",
  "attack_family": "DDOS attack-HOIC",
  "source_ip": "...",
  "destination_ip": "...",
  "ethics_decision": "investigate",
  "final_action": "investigate",
  "audit_logged": true,
  "qauth_assurance_state": "provisional",
  "chronoledger_event_id": "..."
}
```

## B. SOAR Integration

Recommended first targets:

- Shuffle SOAR
- TheHive + Cortex
- DFIR-IRIS

Recommended integration methods:

- Webhook trigger
- Case creation
- Playbook trigger
- Human approval workflow

SOAR playbooks should preserve EthicQ decision controls. Automated response severity should be limited unless EthicQ policy explicitly permits it.

## C. EDR Integration

Recommended future targets:

- Wazuh Agent
- Velociraptor
- osquery
- Sysmon
- Microsoft Defender for Endpoint

Use cases:

- Enrich ORACLE network detections with endpoint telemetry.
- Confirm attack behavior.
- Collect host artifacts.
- Trigger containment recommendations.

## D. Recommended Roadmap

Phase 1 future integration:

- Wazuh SIEM JSON/syslog connector.

Phase 2:

- Shuffle SOAR webhook.

Phase 3:

- osquery, Sysmon, or Velociraptor EDR telemetry adapter.

## E. Security Notes

- SIEM/SOAR/EDR credentials must be stored in environment variables.
- Do not commit API keys or credentials to the repository.
- Outbound alert signing is recommended.
- ChronoLedger event IDs should be included in exported alerts.
- EthicQ should control automatic response severity.
- Oracle Core should remain the integration boundary for outbound alert workflows.
