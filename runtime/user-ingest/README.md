# User Ingest Runtime

This directory stores local runtime helpers for the private ingest setup.

Rules:

- durable ingest state lives in `user/User Wiki/.agent/`
- shared vault state must never be written here
- this runtime directory may hold logs or smoke-test fixtures only
