from alembic import context
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create UUID extension
    context.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create custom types
    context.execute('CREATE TYPE subscription_level AS ENUM (\'free\', \'basic\', \'premium\')')
    context.execute('CREATE TYPE job_status AS ENUM (\'pending\', \'processing\', \'completed\', \'failed\', \'cancelled\')')
    context.execute('CREATE TYPE processing_stage AS ENUM (\'pending\', \'uploading\', \'extracting_audio\', \'speech_recognition\', \'translating\', \'finalizing\', \'completed\')')
    
    # Create users table
    context.execute('''
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            openid VARCHAR(255) UNIQUE,
            email VARCHAR(255) UNIQUE,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255),
            subscription_level subscription_level DEFAULT 'free',
            is_active BOOLEAN DEFAULT true,
            profile JSONB DEFAULT '{}',
            subscription JSONB DEFAULT '{}',
            preferences JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            last_login_at TIMESTAMPTZ
        )
    ''')
    
    # Create media_files table
    context.execute('''
        CREATE TABLE media_files (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            original_name VARCHAR(500) NOT NULL,
            file_name VARCHAR(500) UNIQUE NOT NULL,
            file_path VARCHAR(1000) NOT NULL,
            file_size BIGINT NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            file_type VARCHAR(20) NOT NULL CHECK (file_type IN ('audio', 'video')),
            duration FLOAT,
            format JSONB DEFAULT '{}',
            metadata JSONB DEFAULT '{}',
            storage JSONB DEFAULT '{}',
            processing JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            expires_at TIMESTAMPTZ
        )
    ''')
    
    # Create processing_jobs table
    context.execute('''
        CREATE TABLE processing_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id VARCHAR(255) UNIQUE NOT NULL,
            media_file_id UUID NOT NULL REFERENCES media_files(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            status job_status DEFAULT 'pending',
            progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
            current_stage processing_stage DEFAULT 'pending',
            source_language VARCHAR(10) DEFAULT 'auto',
            target_language VARCHAR(10) NOT NULL,
            result JSONB DEFAULT '{}',
            error JSONB DEFAULT '{}',
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    ''')
    
    # Create transcription_results table
    context.execute('''
        CREATE TABLE transcription_results (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id VARCHAR(255) UNIQUE NOT NULL,
            media_file_id UUID NOT NULL REFERENCES media_files(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            segments JSONB NOT NULL DEFAULT '[]',
            full_text TEXT NOT NULL DEFAULT '',
            language VARCHAR(10) NOT NULL,
            confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
            processing_time INTEGER NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    ''')
    
    # Create indexes
    context.execute('CREATE INDEX idx_users_openid ON users(openid) WHERE openid IS NOT NULL')
    context.execute('CREATE INDEX idx_users_email ON users(email) WHERE email IS NOT NULL')
    context.execute('CREATE INDEX idx_users_username ON users(username)')
    context.execute('CREATE INDEX idx_users_subscription_level ON users(subscription_level)')
    context.execute('CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true')
    context.execute('CREATE INDEX idx_users_profile_gin ON users USING GIN (profile)')
    context.execute('CREATE INDEX idx_users_subscription_gin ON users USING GIN (subscription)')
    context.execute('CREATE INDEX idx_users_premium ON users(id) WHERE subscription_level = \'premium\'')
    
    context.execute('CREATE INDEX idx_media_files_user_id ON media_files(user_id, created_at DESC)')
    context.execute('CREATE INDEX idx_media_files_file_name ON media_files(file_name)')
    context.execute('CREATE INDEX idx_media_files_mime_type ON media_files(mime_type)')
    context.execute('CREATE INDEX idx_media_files_file_type ON media_files(file_type)')
    context.execute('CREATE INDEX idx_media_files_size ON media_files(file_size)')
    context.execute('CREATE INDEX idx_media_files_format_gin ON media_files USING GIN (format)')
    context.execute('CREATE INDEX idx_media_files_metadata_gin ON media_files USING GIN (metadata)')
    context.execute('CREATE INDEX idx_media_files_storage_gin ON media_files USING GIN (storage)')
    context.execute('CREATE INDEX idx_media_files_processing_gin ON media_files USING GIN (processing)')
    
    context.execute('CREATE INDEX idx_processing_jobs_job_id ON processing_jobs(job_id)')
    context.execute('CREATE INDEX idx_processing_jobs_media_file_id ON processing_jobs(media_file_id)')
    context.execute('CREATE INDEX idx_processing_jobs_user_id ON processing_jobs(user_id)')
    context.execute('CREATE INDEX idx_processing_jobs_status ON processing_jobs(status)')
    context.execute('CREATE INDEX idx_processing_jobs_stage ON processing_jobs(current_stage)')
    context.execute('CREATE INDEX idx_processing_jobs_created_at ON processing_jobs(created_at DESC)')
    context.execute('CREATE INDEX idx_processing_jobs_user_status ON processing_jobs(user_id, status)')
    context.execute('CREATE INDEX idx_processing_jobs_status_created ON processing_jobs(status, created_at DESC)')
    context.execute('CREATE INDEX idx_processing_jobs_active_jobs ON processing_jobs(id) WHERE status IN (\'pending\', \'processing\')')
    context.execute('CREATE INDEX idx_processing_jobs_result_gin ON processing_jobs USING GIN (result)')
    context.execute('CREATE INDEX idx_processing_jobs_error_gin ON processing_jobs USING GIN (error)')
    
    context.execute('CREATE INDEX idx_transcription_results_job_id ON transcription_results(job_id)')
    context.execute('CREATE INDEX idx_transcription_results_media_file_id ON transcription_results(media_file_id)')
    context.execute('CREATE INDEX idx_transcription_results_user_id ON transcription_results(user_id, created_at DESC)')
    context.execute('CREATE INDEX idx_transcription_results_language ON transcription_results(language)')
    context.execute('CREATE INDEX idx_transcription_results_confidence ON transcription_results(confidence)')
    context.execute('CREATE INDEX idx_transcription_results_full_text_gin ON transcription_results USING GIN (to_tsvector(\'english\', full_text))')
    context.execute('CREATE INDEX idx_transcription_results_segments_gin ON transcription_results USING GIN (segments)')
    context.execute('CREATE INDEX idx_transcription_results_metadata_gin ON transcription_results USING GIN (metadata)')
    context.execute('CREATE INDEX idx_transcription_results_high_confidence ON transcription_results(id) WHERE confidence > 0.8')

def downgrade() -> None:
    # Drop tables
    context.execute('DROP TABLE IF EXISTS transcription_results')
    context.execute('DROP TABLE IF EXISTS processing_jobs')
    context.execute('DROP TABLE IF EXISTS media_files')
    context.execute('DROP TABLE IF EXISTS users')
    
    # Drop custom types
    context.execute('DROP TYPE IF EXISTS processing_stage')
    context.execute('DROP TYPE IF EXISTS job_status')
    context.execute('DROP TYPE IF EXISTS subscription_level')
    
    # Drop extension
    context.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')