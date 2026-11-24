# DockScope Host Agent (Planned for Milestone 03)

## Architectural Overview

The **DockScope Agent** is an upcoming ultra-lightweight, standalone daemon engineered for zero-dependency deployment across bare-metal Linux servers and remote Docker hosts.

### Core Objectives (Milestone 03)

- **Zero-Friction Enrollment**: Single-command curl-to-shell installer with tokenized authentication.
- **Low Footprint**: Sub-15MB RSS memory utilization, minimal CPU cycles.
- **Bi-directional Security**: Outbound mTLS or WebSocket tunnel to the DockScope controller; no inbound ports required on managed nodes.
- **Telemetry Collection**:
  - Linux kernel metrics (CPU, load average, disk I/O, network bandwidth, memory pressure).
  - Docker daemon events via local unix domain socket `/var/run/docker.sock`.
  - Process tables and container resource consumption.

### Status

This directory is an architectural extension point. The agent binary and distribution pipelines will be implemented during **Milestone 03: Linux Agent & Multi-Host Architecture**.
