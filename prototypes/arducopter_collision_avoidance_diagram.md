# ArduCopter Collision Avoidance

## State Diagram

```mermaid
stateDiagram-v2
    state "Active" as s0
    state "Avoid" as s1
    state "Inactive" as s2
    [*] --> s2
    s0 --> s2 : control_tick [active_inhibited] [priority 0]
    s0 --> s1 : control_tick [avoidance_requested] [priority 10]
    s1 --> s2 : control_tick [avoid_inhibited] [priority 0]
    s1 --> s1 : control_tick [guided_update_ready] [priority 10]
    s1 --> s2 : control_tick [traffic_confirmed_clear] [priority 20]
    s2 --> s0 : control_tick [activation_ready] [priority 10]
```

## State Adjacency Matrix

| → | Active | Avoid | Inactive |
|---|---|---|---|
| **Active** | — | `control_tick` [priority 10] | `control_tick` [priority 0] |
| **Avoid** | — | `control_tick` [priority 10] | `control_tick` [priority 0], `control_tick` [priority 20] |
| **Inactive** | `control_tick` [priority 10] | — | — |

## Transitions

| # | From | Event | To | Priority |
|---|------|-------|----|----------|
| 0 | Active | `control_tick` | Inactive | 0 |
| 1 | Active | `control_tick` | Avoid | 10 |
| 2 | Avoid | `control_tick` | Inactive | 0 |
| 3 | Avoid | `control_tick` | Avoid | 10 |
| 4 | Avoid | `control_tick` | Inactive | 20 |
| 5 | Inactive | `control_tick` | Active | 10 |
