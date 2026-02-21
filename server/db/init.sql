-- =============================================================================
-- FiberQ Database Schema
-- =============================================================================
-- This script initializes the FiberQ PostGIS database with all tables.
-- It runs automatically on first container start via docker-entrypoint-initdb.d.
-- =============================================================================

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create fiberq schema
CREATE SCHEMA IF NOT EXISTS fiberq;
SET search_path TO fiberq, public;

-- =============================================================================
-- PROJECTS
-- =============================================================================

CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    bounds_geom GEOMETRY(Polygon, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by_sub TEXT,
    _modified_by_sub TEXT,
    _modified_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- EXISTING FIBERQ INFRASTRUCTURE TABLES
-- =============================================================================

-- Manholes (OKNA)
CREATE TABLE ftth_okna (
    id SERIAL PRIMARY KEY,
    naziv TEXT,
    tip TEXT,
    broj_okna TEXT,
    adresa_ulica TEXT,
    adresa_broj TEXT,
    stanje TEXT DEFAULT 'Planned',
    godina_ugradnje INTEGER DEFAULT EXTRACT(YEAR FROM NOW()),
    napomena TEXT,
    project_id INTEGER REFERENCES projects(id),
    geom GEOMETRY(Point, 4326),
    _modified_by_sub TEXT,
    _modified_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ftth_okna_geom ON ftth_okna USING GIST (geom);

-- Poles (Stubovi)
CREATE TABLE ftth_stubovi (
    id SERIAL PRIMARY KEY,
    naziv TEXT,
    tip TEXT,
    visina REAL,
    materijal TEXT,
    stanje TEXT DEFAULT 'Planned',
    godina_ugradnje INTEGER DEFAULT EXTRACT(YEAR FROM NOW()),
    napomena TEXT,
    project_id INTEGER REFERENCES projects(id),
    geom GEOMETRY(Point, 4326),
    _modified_by_sub TEXT,
    _modified_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ftth_stubovi_geom ON ftth_stubovi USING GIST (geom);

-- Underground cables (Kablovi podzemni)
CREATE TABLE ftth_kablovi_podzemni (
    id SERIAL PRIMARY KEY,
    naziv TEXT,
    tip TEXT,
    podtip TEXT,
    kapacitet TEXT,
    broj_cevcica INTEGER,
    broj_vlakana INTEGER,
    tip_kabla TEXT,
    vrsta_vlakana TEXT,
    color_code TEXT,
    od TEXT,
    do_ TEXT,
    relacija TEXT,
    duzina_m REAL,
    slack_m REAL DEFAULT 0,
    total_len_m REAL,
    stanje TEXT DEFAULT 'Planned',
    godina_ugradnje INTEGER DEFAULT EXTRACT(YEAR FROM NOW()),
    napomena TEXT,
    project_id INTEGER REFERENCES projects(id),
    geom GEOMETRY(LineString, 4326),
    _modified_by_sub TEXT,
    _modified_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ftth_kablovi_podzemni_geom ON ftth_kablovi_podzemni USING GIST (geom);

-- Aerial cables (Kablovi nadzemni / vazdusni)
CREATE TABLE ftth_kablovi_nadzemni (
    id SERIAL PRIMARY KEY,
    naziv TEXT,
    tip TEXT,
    podtip TEXT,
    kapacitet TEXT,
    broj_cevcica INTEGER,
    broj_vlakana INTEGER,
    tip_kabla TEXT,
    vrsta_vlakana TEXT,
    color_code TEXT,
    od TEXT,
    do_ TEXT,
    relacija TEXT,
    duzina_m REAL,
    slack_m REAL DEFAULT 0,
    total_len_m REAL,
    stanje TEXT DEFAULT 'Planned',
    godina_ugradnje INTEGER DEFAULT EXTRACT(YEAR FROM NOW()),
    napomena TEXT,
    project_id INTEGER REFERENCES projects(id),
    geom GEOMETRY(LineString, 4326),
    _modified_by_sub TEXT,
    _modified_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ftth_kablovi_nadzemni_geom ON ftth_kablovi_nadzemni USING GIST (geom);

-- Routes (Trase)
CREATE TABLE ftth_trase (
    id SERIAL PRIMARY KEY,
    naziv TEXT,
    tip_trase TEXT,
    duzina_m REAL,
    stanje TEXT DEFAULT 'Planned',
    napomena TEXT,
    project_id INTEGER REFERENCES projects(id),
    geom GEOMETRY(LineString, 4326),
    _modified_by_sub TEXT,
    _modified_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ftth_trase_geom ON ftth_trase USING GIST (geom);

-- PE pipes / ducts (Cevi)
CREATE TABLE ftth_cevi (
    id SERIAL PRIMARY KEY,
    naziv TEXT,
    tip TEXT,
    materijal TEXT,
    fi REAL,
    kapacitet TEXT,
    duzina_m REAL,
    stanje TEXT DEFAULT 'Planned',
    napomena TEXT,
    project_id INTEGER REFERENCES projects(id),
    geom GEOMETRY(LineString, 4326),
    _modified_by_sub TEXT,
    _modified_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ftth_cevi_geom ON ftth_cevi USING GIST (geom);

-- Joint closures / connections (Mufovi / Nastavci)
CREATE TABLE ftth_mufovi (
    id SERIAL PRIMARY KEY,
    naziv TEXT,
    tip TEXT,
    kapacitet TEXT,
    stanje TEXT DEFAULT 'Planned',
    godina_ugradnje INTEGER DEFAULT EXTRACT(YEAR FROM NOW()),
    napomena TEXT,
    project_id INTEGER REFERENCES projects(id),
    geom GEOMETRY(Point, 4326),
    _modified_by_sub TEXT,
    _modified_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ftth_mufovi_geom ON ftth_mufovi USING GIST (geom);

-- Fiber breaks / optical reserves (Spojevi)
CREATE TABLE ftth_spojevi (
    id SERIAL PRIMARY KEY,
    naziv TEXT,
    tip TEXT,
    kabl_layer_id TEXT,
    kabl_fid INTEGER,
    duzina_m REAL,
    lokacija TEXT,
    strana TEXT,
    distance_m REAL,
    segments_hit INTEGER,
    vreme TIMESTAMPTZ,
    napomena TEXT,
    project_id INTEGER REFERENCES projects(id),
    geom GEOMETRY(Point, 4326),
    _modified_by_sub TEXT,
    _modified_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ftth_spojevi_geom ON ftth_spojevi USING GIST (geom);

-- =============================================================================
-- NETWORK ELEMENTS (ODF, OTB, TB, TO, Patch Panel)
-- =============================================================================

CREATE TABLE ftth_elements (
    id SERIAL PRIMARY KEY,
    naziv TEXT,
    tip TEXT,
    proizvodjac TEXT,
    oznaka TEXT,
    kapacitet INTEGER,
    ukupno_kj INTEGER,
    zahtev_kapaciteta INTEGER,
    zahtev_rezerve INTEGER,
    oznaka_izvoda TEXT,
    numeracija TEXT,
    naziv_objekta TEXT,
    adresa_ulica TEXT,
    adresa_broj TEXT,
    address_id TEXT,
    stanje TEXT DEFAULT 'Planned',
    godina_ugradnje INTEGER DEFAULT EXTRACT(YEAR FROM NOW()),
    napomena TEXT,
    project_id INTEGER REFERENCES projects(id),
    geom GEOMETRY(Point, 4326),
    _modified_by_sub TEXT,
    _modified_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ftth_elements_geom ON ftth_elements USING GIST (geom);

-- =============================================================================
-- FIBER SPLICE PLAN TABLES
-- =============================================================================

-- Splice closures (муфи с детайли за тавички)
CREATE TABLE fiber_splice_closures (
    id SERIAL PRIMARY KEY,
    muf_fid INTEGER REFERENCES ftth_mufovi(id),
    closure_type TEXT,
    closure_model TEXT,
    tray_count INTEGER DEFAULT 0,
    max_splices INTEGER,
    project_id INTEGER REFERENCES projects(id),
    geom GEOMETRY(Point, 4326),
    _modified_by_sub TEXT,
    _modified_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_fiber_splice_closures_geom ON fiber_splice_closures USING GIST (geom);

-- Splice trays (тавички в муфа)
CREATE TABLE fiber_splice_trays (
    id SERIAL PRIMARY KEY,
    closure_id INTEGER REFERENCES fiber_splice_closures(id) ON DELETE CASCADE,
    tray_number INTEGER NOT NULL,
    tray_type TEXT,
    capacity INTEGER DEFAULT 12,
    UNIQUE (closure_id, tray_number)
);

-- Individual fiber splices (заварки)
CREATE TABLE fiber_splices (
    id SERIAL PRIMARY KEY,
    tray_id INTEGER REFERENCES fiber_splice_trays(id) ON DELETE CASCADE,
    position_in_tray INTEGER NOT NULL,
    -- Side A (incoming cable)
    cable_a_layer_id TEXT,
    cable_a_fid INTEGER,
    fiber_a_number INTEGER,
    fiber_a_color TEXT,
    tube_a_number INTEGER,
    tube_a_color TEXT,
    -- Side B (outgoing cable)
    cable_b_layer_id TEXT,
    cable_b_fid INTEGER,
    fiber_b_number INTEGER,
    fiber_b_color TEXT,
    tube_b_number INTEGER,
    tube_b_color TEXT,
    -- Splice details
    splice_type TEXT DEFAULT 'fusion',
    loss_db REAL,
    status TEXT DEFAULT 'planned',
    spliced_by_sub TEXT,
    spliced_at TIMESTAMPTZ,
    notes TEXT,
    photo_path TEXT,
    _modified_by_sub TEXT,
    _modified_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (tray_id, position_in_tray)
);

-- Patch connections (ODF/OTB port-to-fiber mappings)
CREATE TABLE fiber_patch_connections (
    id SERIAL PRIMARY KEY,
    element_layer_id TEXT,
    element_fid INTEGER,
    port_number INTEGER NOT NULL,
    fiber_cable_layer_id TEXT,
    fiber_cable_fid INTEGER,
    fiber_number INTEGER,
    fiber_color TEXT,
    connector_type TEXT DEFAULT 'SC/APC',
    status TEXT DEFAULT 'free',
    connected_to_patch_id INTEGER REFERENCES fiber_patch_connections(id),
    _modified_by_sub TEXT,
    _modified_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fiber paths (cached end-to-end OLT→ONU traces)
CREATE TABLE fiber_paths (
    id SERIAL PRIMARY KEY,
    path_name TEXT NOT NULL,
    olt_element_fid INTEGER,
    olt_port_number INTEGER,
    onu_element_fid INTEGER,
    onu_port_number INTEGER,
    total_loss_db REAL,
    total_length_m REAL,
    path_segments JSONB,
    status TEXT DEFAULT 'planned',
    project_id INTEGER REFERENCES projects(id),
    _modified_by_sub TEXT,
    _modified_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- WORK ORDERS + SMR REPORTING
-- =============================================================================

-- Work orders
CREATE TABLE work_orders (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    order_type TEXT NOT NULL,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'created',
    project_id INTEGER REFERENCES projects(id),
    assigned_to_sub TEXT,
    assigned_by_sub TEXT,
    area_geom GEOMETRY(Polygon, 4326),
    due_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    verified_at TIMESTAMPTZ,
    verified_by_sub TEXT,
    _modified_by_sub TEXT,
    _modified_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_work_orders_area_geom ON work_orders USING GIST (area_geom);
CREATE INDEX idx_work_orders_assigned ON work_orders (assigned_to_sub);
CREATE INDEX idx_work_orders_status ON work_orders (status);

-- Work order items (individual tasks within a work order)
CREATE TABLE work_order_items (
    id SERIAL PRIMARY KEY,
    work_order_id INTEGER REFERENCES work_orders(id) ON DELETE CASCADE,
    item_type TEXT NOT NULL,
    description TEXT,
    target_layer TEXT,
    target_fid INTEGER,
    quantity REAL,
    unit TEXT,
    status TEXT DEFAULT 'pending',
    completed_at TIMESTAMPTZ,
    completed_by_sub TEXT,
    notes TEXT
);

-- Construction activity reports (SMR)
CREATE TABLE smr_reports (
    id SERIAL PRIMARY KEY,
    work_order_id INTEGER REFERENCES work_orders(id),
    reported_by_sub TEXT NOT NULL,
    report_date DATE DEFAULT CURRENT_DATE,
    weather TEXT,
    crew_size INTEGER,
    hours_worked REAL,
    activities JSONB DEFAULT '[]'::jsonb,
    materials_used JSONB DEFAULT '[]'::jsonb,
    issues TEXT,
    geom GEOMETRY(Point, 4326),
    _modified_by_sub TEXT,
    _modified_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_smr_reports_geom ON smr_reports USING GIST (geom);

-- Field photos
CREATE TABLE field_photos (
    id SERIAL PRIMARY KEY,
    related_type TEXT NOT NULL,
    related_id INTEGER NOT NULL,
    photo_path TEXT NOT NULL,
    caption TEXT,
    taken_at TIMESTAMPTZ DEFAULT NOW(),
    geom GEOMETRY(Point, 4326),
    taken_by_sub TEXT
);
CREATE INDEX idx_field_photos_geom ON field_photos USING GIST (geom);
CREATE INDEX idx_field_photos_related ON field_photos (related_type, related_id);

-- =============================================================================
-- SYNC AUDIT LOG
-- =============================================================================

CREATE TABLE sync_log (
    id SERIAL PRIMARY KEY,
    user_sub TEXT NOT NULL,
    project_id INTEGER REFERENCES projects(id),
    sync_type TEXT NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    features_uploaded INTEGER DEFAULT 0,
    features_downloaded INTEGER DEFAULT 0,
    conflicts_resolved INTEGER DEFAULT 0,
    status TEXT DEFAULT 'in_progress',
    details JSONB
);

-- =============================================================================
-- GRANTS (for the fiberq user)
-- =============================================================================

GRANT USAGE ON SCHEMA fiberq TO fiberq;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA fiberq TO fiberq;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA fiberq TO fiberq;
ALTER DEFAULT PRIVILEGES IN SCHEMA fiberq GRANT ALL PRIVILEGES ON TABLES TO fiberq;
ALTER DEFAULT PRIVILEGES IN SCHEMA fiberq GRANT ALL PRIVILEGES ON SEQUENCES TO fiberq;

-- =============================================================================
-- USER LOGIN TRACKING
-- =============================================================================
-- Tracks last login time per user since Kanidm does not expose this via API.
-- Updated on each WebUI or QGIS plugin authentication.

CREATE TABLE IF NOT EXISTS user_logins (
    user_sub TEXT PRIMARY KEY,
    username TEXT,
    last_login_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    login_source TEXT DEFAULT 'web'
);
CREATE INDEX IF NOT EXISTS idx_user_logins_last ON user_logins (last_login_at);
