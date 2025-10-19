# Data Model Design: Mini-Program Media Translation Tool

**Created**: 2025-10-18  
**Status**: Design Phase Complete  
**Purpose**: Database schema and data flow design for uni-app + FastAPI development

## Database Schema Design

### PostgreSQL Schema

```sql
-- Users table - Core user accounts
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    openid VARCHAR(128) UNIQUE NOT NULL,           -- WeChat OpenID
    unionid VARCHAR(128),                          -- WeChat UnionID (optional)
    username VARCHAR(100),                         -- Display username
    avatar_url VARCHAR(1024),                      -- User avatar
    phone VARCHAR(20),                             -- Phone number (optional)
    email VARCHAR(255),                            -- Email (optional)
    
    -- Subscription fields
    subscription_level VARCHAR(50) DEFAULT 'free', -- free, basic_vip, premium_vip
    subscription_expires_at TIMESTAMP,              -- VIP expiration time
    
    -- Quota management
    quota_used INTEGER DEFAULT 0,                 -- Used quota in current period
    quota_limit INTEGER DEFAULT 1,                -- Total quota limit for current period
    quota_reset_date DATE,                        -- Date when quota resets
    
    -- Status and timestamps
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Subscription plans table
CREATE TABLE subscription_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,                   -- Basic VIP, Premium VIP
    code VARCHAR(50) UNIQUE NOT NULL,             -- basic_vip, premium_vip
    price DECIMAL(10,2) NOT NULL,                 -- Monthly price
    quota_limit INTEGER NOT NULL,                 -- Translations per month
    description TEXT,
    features JSONB,                               -- Feature list as JSON
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Payment orders table
CREATE TABLE payment_orders (
    id SERIAL PRIMARY KEY,
    order_no VARCHAR(64) UNIQUE NOT NULL,         -- Unique order number
    user_id INTEGER REFERENCES users(id),
    plan_id INTEGER REFERENCES subscription_plans(id),
    
    -- Payment details
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CNY',
    payment_method VARCHAR(50),                    -- wechat_pay, alipay, etc.
    payment_status VARCHAR(50) DEFAULT 'pending', -- pending, paid, failed, refunded
    
    -- WeChat Pay specific fields
    prepay_id VARCHAR(128),                       -- WeChat prepay ID
    transaction_id VARCHAR(128),                  -- WeChat transaction ID
    
    -- Timestamps
    paid_at TIMESTAMP,
    refunded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Translation tasks table
CREATE TABLE translation_tasks (
    id SERIAL PRIMARY KEY,
    task_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id),
    
    -- Source media information
    original_filename VARCHAR(255),
    original_file_url VARCHAR(1024),
    file_size BIGINT,                             -- File size in bytes
    file_type VARCHAR(50),                        -- audio, video, wechat_video, link
    mime_type VARCHAR(100),
    duration_seconds FLOAT,                       -- Audio/video duration
    
    -- Processing information
    processing_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    processing_error TEXT,                        -- Error message if failed
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    
    -- Results
    transcribed_text TEXT,
    confidence_score FLOAT,                       -- Transcription confidence 0-1
    word_count INTEGER,                           -- Word count of transcription
    
    -- Third-party service info
    service_provider VARCHAR(100),                -- alibaba_cloud, tencent_cloud, etc.
    service_request_id VARCHAR(128),              -- External service request ID
    service_cost DECIMAL(10,4),                   -- Cost of external service
    
    -- Usage tracking
    is_quota_used BOOLEAN DEFAULT FALSE,          -- Whether quota was deducted
    quota_deducted_at TIMESTAMP,
    
    -- Metadata
    metadata JSONB,                               -- Additional metadata as JSON
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Usage statistics table
CREATE TABLE usage_statistics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    date DATE NOT NULL,
    
    -- Daily usage metrics
    translations_completed INTEGER DEFAULT 0,
    total_duration_seconds FLOAT DEFAULT 0,
    total_file_size BIGINT DEFAULT 0,
    quota_consumed INTEGER DEFAULT 0,
    
    -- Cost tracking
    service_cost_total DECIMAL(10,4) DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, date)                        -- One record per user per day
);

-- System settings table
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    data_type VARCHAR(50) DEFAULT 'string',       -- string, number, boolean, json
    is_public BOOLEAN DEFAULT FALSE,              -- Whether setting is exposed to frontend
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Audit log table
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),         -- Can be NULL for system actions
    action VARCHAR(100) NOT NULL,                 -- login, logout, translate, upgrade, etc.
    resource_type VARCHAR(100),                   -- user, translation, payment, etc.
    resource_id VARCHAR(100),                     -- ID of affected resource
    details JSONB,                                -- Action details as JSON
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_users_openid ON users(openid);
CREATE INDEX idx_users_subscription ON users(subscription_level);
CREATE INDEX idx_translation_tasks_user_id ON translation_tasks(user_id);
CREATE INDEX idx_translation_tasks_status ON translation_tasks(processing_status);
CREATE INDEX idx_translation_tasks_created_at ON translation_tasks(created_at);
CREATE INDEX idx_payment_orders_user_id ON payment_orders(user_id);
CREATE INDEX idx_payment_orders_status ON payment_orders(payment_status);
CREATE INDEX idx_usage_statistics_user_date ON usage_statistics(user_id, date);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

## Data Flow Architecture

### uni-app Frontend Data Flow

```typescript
// Store Management with Pinia
interface UserState {
  user: User | null;
  isLoggedIn: boolean;
  quota: {
    used: number;
    limit: number;
    resetDate: Date;
  };
}

interface TranslationState {
  tasks: TranslationTask[];
  currentTask: TranslationTask | null;
  isProcessing: boolean;
}

// API Service Layer
class ApiService {
  // User authentication
  async loginByWechat(): Promise<AuthResponse>
  async getUserInfo(): Promise<User>
  async logout(): Promise<void>
  
  // Translation management
  async uploadFile(file: File): Promise<UploadResponse>
  async startTranslation(taskData: TranslationRequest): Promise<TranslationTask>
  async getTranslationStatus(taskId: string): Promise<TranslationTask>
  async getTranslationHistory(page: number): Promise<TranslationHistory>
  
  // Payment and subscription
  async getSubscriptionPlans(): Promise<SubscriptionPlan[]>
  async createOrder(planId: string): Promise<PaymentOrder>
  async initiateWechatPayment(orderId: string): Promise<WechatPaymentData>
}
```

### FastAPI Backend Data Flow

```python
# Pydantic Models for API
class UserBase(BaseModel):
    username: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    openid: str
    unionid: Optional[str] = None

class UserResponse(UserBase):
    id: int
    subscription_level: str
    quota_used: int
    quota_limit: int
    quota_reset_date: Optional[date]
    
class TranslationRequest(BaseModel):
    file_type: str
    original_filename: str
    file_size: int
    file_url: str
    
class TranslationResponse(BaseModel):
    task_id: str
    status: str
    transcribed_text: Optional[str] = None
    confidence_score: Optional[float] = None

# Database Models with SQLAlchemy
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    openid = Column(String(128), unique=True, nullable=False)
    subscription_level = Column(String(50), default="free")
    quota_used = Column(Integer, default=0)
    quota_limit = Column(Integer, default=1)
    
    # Relationships
    translations = relationship("TranslationTask", back_populates="user")
    orders = relationship("PaymentOrder", back_populates="user")

class TranslationTask(Base):
    __tablename__ = "translation_tasks"
    
    id = Column(Integer, primary_key=True)
    task_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    processing_status = Column(String(50), default="pending")
    transcribed_text = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="translations")
```

## Migration Mapping: MongoDB to PostgreSQL

### Document-Based to Relational Mapping

**Original MongoDB Document**:
```javascript
{
  _id: ObjectId("..."),
  openid: "wx123...",
  username: "张三",
  subscription: {
    level: "basic_vip",
    expiresAt: ISODate("2024-12-31"),
    quota: {
      used: 5,
      limit: 10,
      resetDate: ISODate("2024-12-01")
    }
  },
  translations: [
    {
      filename: "audio.mp3",
      text: "转录的文本内容...",
      duration: 120.5,
      createdAt: ISODate("2024-11-15T10:30:00Z")
    }
  ],
  createdAt: ISODate("2024-11-01T08:00:00Z")
}
```

**Migrated PostgreSQL Tables**:
```sql
-- Users table
INSERT INTO users (openid, username, subscription_level, subscription_expires_at, 
                   quota_used, quota_limit, quota_reset_date, created_at)
VALUES ('wx123...', '张三', 'basic_vip', '2024-12-31', 5, 10, '2024-12-01', '2024-11-01');

-- Translation tasks table
INSERT INTO translation_tasks (user_id, original_filename, transcribed_text, 
                              duration_seconds, processing_status, created_at)
VALUES (1, 'audio.mp3', '转录的文本内容...', 120.5, 'completed', '2024-11-15 10:30:00');
```

## Data Validation Strategy

### Migration Validation Scripts

```python
class DataValidator:
    def validate_user_migration(self, mongo_count: int, pg_count: int) -> bool:
        """Validate user count matches between MongoDB and PostgreSQL"""
        return mongo_count == pg_count
    
    def validate_translation_data(self, user_id: int) -> bool:
        """Validate translation data integrity for a user"""
        mongo_translations = self.mongo_db.translations.find({"userId": user_id})
        pg_translations = self.pg_session.query(TranslationTask).filter(
            TranslationTask.user_id == user_id
        ).all()
        
        return len(mongo_translations) == len(pg_translations)
    
    def validate_quota_consistency(self, user_id: int) -> bool:
        """Validate quota data consistency"""
        mongo_user = self.mongo_db.users.find_one({"_id": user_id})
        pg_user = self.pg_session.query(User).filter(User.id == user_id).first()
        
        return (mongo_user["subscription"]["quota"]["used"] == pg_user.quota_used and
                mongo_user["subscription"]["quota"]["limit"] == pg_user.quota_limit)
```

## Performance Optimization

### Database Optimization Strategies

1. **Indexing Strategy**:
   - Primary indexes on foreign keys
   - Composite indexes on common query patterns
   - Partial indexes for specific filtering scenarios

2. **Query Optimization**:
   - Use connection pooling for high concurrency
   - Implement read replicas for reporting queries
   - Cache frequently accessed data (user info, subscription plans)

3. **Data Partitioning**:
   - Partition translation_tasks by date for large datasets
   - Consider table partitioning for audit_logs by month

### Caching Strategy

```python
# Redis caching for frequently accessed data
@lru_cache(maxsize=1000)
async def get_user_subscription(user_id: int) -> UserSubscription:
    """Cache user subscription data"""
    return await user_service.get_subscription(user_id)

# Cache invalidation strategy
async def update_user_quota(user_id: int, new_quota: int):
    """Update quota and invalidate cache"""
    await user_service.update_quota(user_id, new_quota)
    get_user_subscription.cache_clear()
```

## Security Considerations

### Data Protection
1. **Encryption**:
   - Encrypt sensitive data at rest (phone numbers, email)
   - Use TLS for all data in transit
   - Implement application-level encryption for transcription data

2. **Access Control**:
   - Row-level security for user data isolation
   - API rate limiting to prevent abuse
   - Audit logging for all data access

3. **Privacy Compliance**:
   - Implement data retention policies
   - Provide data export functionality
   - Secure data deletion processes

## Backup and Recovery

### Backup Strategy
1. **Regular Backups**:
   - Daily full backups with point-in-time recovery
   - Continuous WAL archiving for minimal data loss
   - Cross-region backup replication

2. **Migration Backup**:
   - Final MongoDB backup before migration
   - PostgreSQL backup after each migration phase
   - Rollback procedures for each migration step

This data model design ensures a robust, scalable, and maintainable foundation for the uni-app and FastAPI migration while maintaining data integrity and performance.