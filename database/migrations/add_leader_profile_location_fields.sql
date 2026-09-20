-- Additive only. Safe on a running database.
-- Does not DROP, rewrite, or delete any rows.
-- Age is NOT stored; the app calculates it from date_of_birth.
-- Already applied on the shared Supabase project; kept here for repo history.

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users') THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'address'
        ) THEN
            ALTER TABLE users ADD COLUMN address TEXT;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'district'
        ) THEN
            ALTER TABLE users ADD COLUMN district TEXT;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'province'
        ) THEN
            ALTER TABLE users ADD COLUMN province TEXT;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'date_of_birth'
        ) THEN
            ALTER TABLE users ADD COLUMN date_of_birth DATE;
        END IF;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_users_district ON users (district);
CREATE INDEX IF NOT EXISTS idx_users_province ON users (province);
