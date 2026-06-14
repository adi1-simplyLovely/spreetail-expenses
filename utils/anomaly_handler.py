"""Anomaly handler — applies the documented policy for each detected anomaly.
Returns the action taken (IMPORTED/SKIPPED/FLAGGED/CONVERTED/AS_SETTLEMENT)
and a modified row ready for database insertion."""
