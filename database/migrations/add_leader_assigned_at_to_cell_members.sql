-- When this person was assigned to the current leader_id.
-- created_at stays the first time the row was created and does not change
-- on transfer, reassign, or promote.
-- Safe/idempotent: only fills leader_assigned_at when it is still null.
-- Does not touch attendance rows.

ALTER TABLE cell_members
    ADD COLUMN IF NOT EXISTS leader_assigned_at TIMESTAMPTZ;

COMMENT ON COLUMN cell_members.leader_assigned_at IS
    'When this person was assigned to the current leader_id. Roster join date is this value, or created_at when it is null. Do not edit by hand on a normal member update.';

UPDATE cell_members
SET leader_assigned_at = created_at
WHERE leader_assigned_at IS NULL
  AND created_at IS NOT NULL;

-- ---------------------------------------------------------------------------
-- ROLLBACK (uncomment to revert the column only; do not delete attendance):
-- ALTER TABLE cell_members DROP COLUMN IF EXISTS leader_assigned_at;
