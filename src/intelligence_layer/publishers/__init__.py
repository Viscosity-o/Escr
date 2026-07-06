"""
publishers/
===========
Responsible for forwarding normalized IntelligenceRecords to
downstream systems for further processing.

This layer is the exit point of the Global Intelligence Layer module.
It does not care about what happens to the data after it is forwarded.

Publisher responsibilities:
  - Serialize IntelligenceRecords into a wire format (JSON, Avro, Protobuf, etc.)
  - Forward to the configured downstream target (message queue, HTTP endpoint, file, etc.)
  - Handle delivery acknowledgments and transient failures with retry logic
  - Log publish success/failure for observability

Multiple publisher implementations can coexist to support different targets
(e.g., a file-based publisher for local development, a queue publisher for production).
All implementations must conform to BasePublisher.
"""
