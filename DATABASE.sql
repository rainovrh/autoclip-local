-- =====================================================================
-- DATABASE.sql — AutoClip Local
-- =====================================================================
-- Skema ini dirancang untuk arsitektur Single-User / Local Admin
-- sesuai SPECIFICATION.md. Ditulis dalam dialek SQLite (cocok dengan
-- stack FastAPI lokal), namun tetap portable ke PostgreSQL dengan
-- penyesuaian minor (AUTOINCREMENT -> SERIAL/IDENTITY, TEXT CHECK -> ENUM).
--
-- Aktifkan foreign key enforcement (khusus SQLite):
PRAGMA foreign_keys = ON;

-- =====================================================================
-- RINGKASAN ERD (Entity Relationship Diagram — tekstual)
-- =====================================================================
--
--  projects (1) ───< video_sources (1)
--  projects (1) ───< transcripts (1) ───< transcript_segments ───< transcript_words
--  projects (1) ───< analysis_results (1) ───< highlight_moments
--  highlight_moments (1) ───< clips
--  transcript_segments (referenced by highlight_moments.start/end_segment_id)
--  transcript_words     (referenced by highlight_moments.start/end_word_id)
--  clips (1) ───  subtitle_styles (1:1)
--  clips (1) ───< broll_assets
--  transcript_segments (1) ───< broll_assets (konteks kalimat sumber pencarian Pexels)
--  projects (1) ───< processing_jobs   (antrean FFmpeg -> Whisper -> Ollama -> Render)
--  projects (1) ───< garbage_collection_logs
--  api_keys, app_settings  -> tabel global (tidak terikat project tertentu)
--
-- Catatan desain penting yang mengikuti SPECIFICATION.md:
--  1) State machine proyek disimpan di projects.status (Checkpoint Engine).
--  2) Anti-Halusinasi: highlight_moments TIDAK menyimpan timestamp hasil
--     tebakan LLM. Ia hanya menyimpan referensi FK ke transcript_segments /
--     transcript_words. Timestamp asli tetap bersumber dari Whisper.
--  3) broll_assets punya kolom `status` dengan nilai 'fallback_used' agar
--     arsitektur Non-Blocking Overlay (Pexels gagal -> tetap render
--     center-crop asli) bisa dilacak di riwayat.
--  4) garbage_collection_logs mencatat file temporary (mis. audio .wav)
--     yang dihapus otomatis setelah status proyek menjadi RENDERED.
-- =====================================================================


-- =====================================================================
-- 1. PROJECTS — entitas induk, nama folder output mengikuti judul proyek
-- =====================================================================
CREATE TABLE projects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL UNIQUE,          -- dipakai sebagai nama folder
    folder_path     TEXT NOT NULL UNIQUE,           -- path fisik direktori output
    source_type     TEXT NOT NULL CHECK (source_type IN ('youtube', 'local_upload')),
    source_url      TEXT,                           -- diisi jika source_type = youtube
    original_filename TEXT,                         -- diisi jika source_type = local_upload

    -- Checkpoint Engine / State Machine
    status          TEXT NOT NULL DEFAULT 'UPLOADED'
                    CHECK (status IN (
                        'UPLOADED',
                        'AUDIO_EXTRACTED',
                        'TRANSCRIBED',
                        'ANALYZED',
                        'RENDERED',
                        'FAILED'
                    )),

    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_projects_status ON projects(status);


-- =====================================================================
-- 2. VIDEO_SOURCES — metadata video mentah (hasil unggah / hasil unduh)
-- =====================================================================
CREATE TABLE video_sources (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL UNIQUE
                    REFERENCES projects(id) ON DELETE CASCADE,

    file_path       TEXT NOT NULL,                  -- lokasi video sumber di local storage
    audio_path      TEXT,                            -- lokasi audio .wav hasil ekstraksi (temp)
    resolution      TEXT,                             -- mis. "1920x1080"
    duration_seconds REAL,
    fps             REAL,
    quality_check_passed INTEGER NOT NULL DEFAULT 0 CHECK (quality_check_passed IN (0,1)),

    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);


-- =====================================================================
-- 3. TRANSCRIPTS — hasil Whisper (satu proyek = satu transkrip penuh)
-- =====================================================================
CREATE TABLE transcripts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL UNIQUE
                    REFERENCES projects(id) ON DELETE CASCADE,

    full_text       TEXT NOT NULL,
    language        TEXT,
    whisper_model   TEXT NOT NULL,                  -- mis. "whisper-large-v3"

    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);


-- =====================================================================
-- 4. TRANSCRIPT_SEGMENTS — level kalimat
-- =====================================================================
CREATE TABLE transcript_segments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    transcript_id   INTEGER NOT NULL
                    REFERENCES transcripts(id) ON DELETE CASCADE,

    segment_index   INTEGER NOT NULL,               -- urutan kalimat dalam transkrip
    start_time      REAL NOT NULL,                  -- detik, sumber kebenaran waktu
    end_time        REAL NOT NULL,
    text            TEXT NOT NULL,

    UNIQUE (transcript_id, segment_index)
);

CREATE INDEX idx_segments_transcript ON transcript_segments(transcript_id);


-- =====================================================================
-- 5. TRANSCRIPT_WORDS — level kata (word-level timestamps)
-- =====================================================================
CREATE TABLE transcript_words (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_id      INTEGER NOT NULL
                    REFERENCES transcript_segments(id) ON DELETE CASCADE,

    word_index      INTEGER NOT NULL,               -- urutan kata dalam kalimat
    word            TEXT NOT NULL,
    start_time      REAL NOT NULL,
    end_time        REAL NOT NULL,
    confidence      REAL,                            -- skor akurasi dari Whisper

    UNIQUE (segment_id, word_index)
);

CREATE INDEX idx_words_segment ON transcript_words(segment_id);


-- =====================================================================
-- 6. ANALYSIS_RESULTS — output mentah LLM (Ollama) per proyek
-- =====================================================================
CREATE TABLE analysis_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL
                    REFERENCES projects(id) ON DELETE CASCADE,

    llm_model       TEXT NOT NULL,                  -- mis. "llama3:8b" via Ollama
    raw_json_output TEXT NOT NULL,                  -- respons JSON terstruktur mentah dari LLM

    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_analysis_project ON analysis_results(project_id);


-- =====================================================================
-- 7. HIGHLIGHT_MOMENTS — momen menarik hasil ekstraksi LLM
--    (Anti-Halusinasi: hanya referensi ID kalimat/kata, bukan timestamp)
-- =====================================================================
CREATE TABLE highlight_moments (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id         INTEGER NOT NULL
                        REFERENCES analysis_results(id) ON DELETE CASCADE,

    -- Referensi ke ID kalimat sebagai batas potongan (bukan angka waktu)
    start_segment_id    INTEGER NOT NULL
                        REFERENCES transcript_segments(id),
    end_segment_id      INTEGER NOT NULL
                        REFERENCES transcript_segments(id),

    -- Opsional: presisi ke level kata jika LLM memberi batas lebih halus
    start_word_id       INTEGER REFERENCES transcript_words(id),
    end_word_id         INTEGER REFERENCES transcript_words(id),

    suggested_duration_seconds REAL,                -- durasi otomatis usulan LLM
    engagement_reason   TEXT,                        -- alasan tingkat engagement tinggi
    engagement_score    REAL,

    status              TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'rendered', 'rejected')),

    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_moments_analysis ON highlight_moments(analysis_id);
CREATE INDEX idx_moments_status ON highlight_moments(status);


-- =====================================================================
-- 8. CLIPS — hasil akhir render per momen
-- =====================================================================
CREATE TABLE clips (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL
                        REFERENCES projects(id) ON DELETE CASCADE,
    highlight_moment_id INTEGER NOT NULL
                        REFERENCES highlight_moments(id) ON DELETE CASCADE,

    aspect_ratio        TEXT NOT NULL DEFAULT '9:16'
                        CHECK (aspect_ratio IN ('9:16', '16:9', '4:5', '1:1')),
    crop_mode           TEXT NOT NULL DEFAULT 'center_crop_static',

    output_path         TEXT,
    resolution           TEXT,                        -- resolusi dipertahankan dari sumber
    duration_seconds    REAL,

    render_status        TEXT NOT NULL DEFAULT 'queued'
                        CHECK (render_status IN ('queued', 'rendering', 'completed', 'failed')),
    render_error_message TEXT,

    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at           TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_clips_project ON clips(project_id);
CREATE INDEX idx_clips_moment ON clips(highlight_moment_id);


-- =====================================================================
-- 9. SUBTITLE_STYLES — pengaturan tampilan subtitle per klip (1:1)
-- =====================================================================
CREATE TABLE subtitle_styles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    clip_id         INTEGER NOT NULL UNIQUE
                    REFERENCES clips(id) ON DELETE CASCADE,

    display_mode    TEXT NOT NULL DEFAULT 'word_by_word'
                    CHECK (display_mode IN ('word_by_word', 'full_sentence')),

    font_family     TEXT NOT NULL DEFAULT 'Inter',
    font_size       INTEGER NOT NULL DEFAULT 48,
    font_weight     TEXT NOT NULL DEFAULT 'bold'
                    CHECK (font_weight IN ('regular', 'medium', 'semibold', 'bold', 'black')),

    is_uppercase    INTEGER NOT NULL DEFAULT 0 CHECK (is_uppercase IN (0,1)),

    text_color      TEXT NOT NULL DEFAULT '#FFFFFF',
    highlight_color TEXT NOT NULL DEFAULT '#FFD500', -- warna sorotan kata yang sedang diucapkan
    background_color TEXT,
    background_opacity REAL DEFAULT 0.0,

    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);


-- =====================================================================
-- 10. BROLL_ASSETS — integrasi Dynamic B-Roll via Pexels API
-- =====================================================================
CREATE TABLE broll_assets (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    clip_id             INTEGER NOT NULL
                        REFERENCES clips(id) ON DELETE CASCADE,
    source_segment_id   INTEGER
                        REFERENCES transcript_segments(id), -- konteks kalimat pemicu pencarian

    pexels_query        TEXT,                         -- hasil terjemahan konteks kalimat oleh LLM
    pexels_video_id     TEXT,
    pexels_video_url    TEXT,
    local_cache_path    TEXT,

    overlay_start_time  REAL,                         -- posisi sisip relatif terhadap klip
    overlay_end_time    REAL,

    status               TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'success', 'fallback_used', 'failed')),
    -- 'fallback_used' = Pexels timeout/gagal -> render tetap jalan dengan center-crop asli

    created_at           TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_broll_clip ON broll_assets(clip_id);


-- =====================================================================
-- 11. PROCESSING_JOBS — antrean pemrosesan (queue engine)
--     Hanya satu model AI berat aktif dalam satu waktu:
--     FFmpeg -> Whisper -> Ollama -> Render
-- =====================================================================
CREATE TABLE processing_jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL
                    REFERENCES projects(id) ON DELETE CASCADE,

    job_type        TEXT NOT NULL CHECK (job_type IN (
                        'ffmpeg_extract_audio',
                        'whisper_transcribe',
                        'ollama_analyze',
                        'render_clip'
                    )),

    status          TEXT NOT NULL DEFAULT 'queued'
                    CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    priority        INTEGER NOT NULL DEFAULT 0,

    started_at      TEXT,
    finished_at     TEXT,
    error_message   TEXT,

    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_jobs_status ON processing_jobs(status);
CREATE INDEX idx_jobs_project ON processing_jobs(project_id);


-- =====================================================================
-- 12. GARBAGE_COLLECTION_LOGS — riwayat penghapusan file temporary
--     (mis. .wav mentah) otomatis setelah status proyek = RENDERED
-- =====================================================================
CREATE TABLE garbage_collection_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL
                    REFERENCES projects(id) ON DELETE CASCADE,

    file_path       TEXT NOT NULL,
    file_type       TEXT,                             -- mis. "temp_audio_wav"
    reason          TEXT NOT NULL DEFAULT 'project_status_rendered',

    deleted_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_gc_project ON garbage_collection_logs(project_id);


-- =====================================================================
-- 13. API_KEYS — manajemen kunci API pihak ketiga (Local Admin only)
-- =====================================================================
CREATE TABLE api_keys (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name    TEXT NOT NULL UNIQUE,             -- mis. "pexels"
    api_key_value   TEXT NOT NULL,                    -- disimpan sesuai .env / vault lokal
    is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),

    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);


-- =====================================================================
-- 14. APP_SETTINGS — pengaturan global aplikasi (opsional, key-value)
-- =====================================================================
CREATE TABLE app_settings (
    setting_key     TEXT PRIMARY KEY,
    setting_value   TEXT NOT NULL,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Contoh seed data default (opsional)
INSERT INTO app_settings (setting_key, setting_value) VALUES
    ('default_aspect_ratio', '9:16'),
    ('default_whisper_model', 'large-v3'),
    ('default_ollama_model', 'llama3:8b');
