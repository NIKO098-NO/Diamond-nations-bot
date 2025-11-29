# TODO: Modify Supervise Command and Add Logging/Warnings

## Tasks
- [x] Modify the supervise command in `cogs/supervision.py` to send embed responses instead of plain text.
- [x] Add message logging for supervised users in the `on_message` listener and send logs to supervisor.
- [x] Implement a periodic task to check for users supervised for 30+ days and send status updates to supervisor.
- [x] Test the changes to ensure embeds display correctly and logging/status updates work as expected.
