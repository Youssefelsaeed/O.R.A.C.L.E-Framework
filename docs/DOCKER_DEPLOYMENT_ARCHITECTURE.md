# Docker Deployment Architecture

Docker support is a runtime deployment path for O.R.A.C.L.E Framework Final. It starts the stable operator stack and does not train GAN models, promote candidates, include raw datasets, or bake secrets into images.

## Runtime Services

| Service | Container | Port | Purpose |
| --- | --- | ---: | --- |
| Oracle Core | `oracle-core` | `8000` | Central orchestration API and dashboard API |
| QAuthCore | `qauthcore` | `8001` | Token generation, verification, and assurance |
| EthicQ | `ethicq` | `8002` | Defensive ethics decisioning |
| ChronoLedger | `chronoledger` | `8003` | Runtime audit evidence API |
| GhostTunnel | `ghosttunnel` | `8004` | Safe response transmit/fast-ack runtime |
| Oracle GUI | `oracle-gui` | `4173` | Operator console |

All services run on the `oracle-net` Docker network. Oracle Core calls downstream services by compose service name, for example `http://qauthcore:8001`.

## Volumes

Docker uses host-mounted runtime volumes:

- `./reports:/app/reports`
- `./data:/app/data`
- `./models_candidate:/app/models_candidate`
- `./models_final:/app/models_final:ro`

`models_final` is mounted read-only. Candidate artifacts are read/write because candidate-only evolution and dry-run workflows may write there. Large model binaries are not baked into Docker images.

## Excluded From Images

The Docker context excludes:

- raw datasets, packet captures, and research folders
- `.env`, secrets, keys, virtual environments, and caches
- `node_modules` and GUI build output
- generated reports and logs
- `models_final`, `models_candidate`, and binary model artifacts

Raw datasets remain local-only. If a deployment requires production model binaries, place them on the host and mount them through the documented volumes or a controlled release artifact workflow.

## Monitoring Mode

Live packet capture is not containerized by default. Packet capture on Windows depends on Scapy, Npcap, and administrator permissions, so it remains a host/manual activity.

Realtime replay proof is supported in Docker mode:

```powershell
python scripts/oracle_realtime_replay_proof.py --events 25 --oracle-url http://127.0.0.1:8000
```

## Quick Start

Install Docker Desktop and enable Linux containers.

```powershell
python scripts/docker_oracle_up.py
```

Open:

```text
http://127.0.0.1:4173
```

Check status and logs:

```powershell
python scripts/docker_oracle_status.py
python scripts/docker_oracle_logs.py
```

Run validation:

```powershell
python scripts/test_docker_oracle_runtime.py
```

Stop:

```powershell
python scripts/docker_oracle_down.py
```

## Safety Position

Docker deployment is for runtime operation and demonstration, not training deployment. It does not run GAN training, does not promote models, does not enable SIEM/SOAR/EDR integration, and does not change `models_final`.
