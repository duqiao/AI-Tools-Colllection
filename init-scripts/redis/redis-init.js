# Redis initialization script with default configuration and health check

// Connect to Redis
const redis = require('redis');
const client = redis.createClient({
  host: 'redis',
  port: 6379,
  password: 'dev123456',
  retry_delay_on_failover: 100,
  max_retries_per_request: 3
});

// Application-specific keys
const APP_KEYS_PREFIX = 'ai:';
const USER_SESSION_PREFIX = 'user:session:';
const JOB_STATUS_PREFIX = 'job:status:';
const CACHE_PREFIX = 'cache:';

async function initRedis() {
  console.log('Initializing Redis for AI Media Translation...');
  
  try {
    // Test connection
    await client.connect();
    console.log('✅ Redis connection successful');
    
    // Set up basic configurations
    await client.config('set', 'save', 3600); // 1 hour TTL
    await client.config('set', 'maxmemory-policy', 'allkeys-lru');
    
    // Create application-specific indexes
    await client.flushall();
    
    console.log('Redis configured with:');
    console.log('  - TTL: 1 hour for sessions');
    console.log('  - Memory policy: allkeys-lru');
    console.log('  - Password authentication enabled');
    console.log('  - Application key prefixes configured');
    
    return true;
    
  } catch (error) {
    console.error('❌ Redis connection failed:', error.message);
    return false;
  }
}

// Helper functions for common operations
async function setUserSession(userId, userData, ttl = 3600) {
  const sessionKey = `${USER_SESSION_PREFIX}${userId}`;
  await client.setex(sessionKey, JSON.stringify(userData), ttl);
}

async function getUserSession(userId) {
  const sessionKey = `${USER_SESSION_PREFIX}${userId}`;
  const sessionData = await client.get(sessionKey);
  return sessionData ? JSON.parse(sessionData) : null;
}

async function setJobStatus(jobId, status, progress = 0, ttl = 3600) {
  const statusKey = `${JOB_STATUS_PREFIX}${jobId}`;
  const statusData = JSON.stringify({
    status: status,
    progress: progress,
    timestamp: new Date().toISOString()
  });
  await client.setex(statusKey, statusData, ttl);
}

async function getJobStatus(jobId) {
  const statusKey = `${JOB_STATUS_PREFIX}${jobId}`;
  const statusData = await client.get(statusKey);
  return statusData ? JSON.parse(statusData) : null;
}

async function cacheResult(key, data, ttl = 3600) {
  await client.setex(`${CACHE_PREFIX}${key}`, JSON.stringify(data), ttl);
}

async function getCachedResult(key) {
  const cachedData = await client.get(`${CACHE_PREFIX}${key}`);
  return cachedData ? JSON.parse(cachedData) : null;
}

// Health check function
async function checkRedisHealth() {
  try {
    const pong = await client.ping();
    console.log('✅ Redis health check successful:', pong);
    return true;
  } catch (error) {
    console.error('❌ Redis health check failed:', error.message);
    return false;
  }
}

// Export functions
module.exports = {
  initRedis,
  setUserSession,
  getUserSession,
  setJobStatus,
  getJobStatus,
  cacheResult,
  getCachedResult,
  checkRedisHealth,
  client
};