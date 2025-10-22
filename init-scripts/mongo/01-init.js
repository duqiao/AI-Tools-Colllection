// MongoDB initialization script for ai_media_translation database
db = db.getSiblingDB('ai_media_translation');

// Create collections with validation
db.createCollection('media_files', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['original_name', 'file_name', 'file_path', 'mime_type', 'file_size', 'upload_date', 'uploaded_by'],
      properties: {
        original_name: {
          bsonType: 'string',
          description: 'Original file name before upload'
        },
        file_name: {
          bsonType: 'string',
          description: 'Generated file name'
        },
        file_path: {
          bsonType: 'string',
          description: 'Storage path for the file'
        },
        mime_type: {
          bsonType: 'string',
          enum: ['audio/mpeg', 'audio/wav', 'audio/mp3', 'video/mp4', 'video/avi', 'video/mov']
        },
        file_size: {
          bsonType: 'number',
          minimum: 1,
          maximum: 104857600
        },
        upload_date: {
          bsonType: 'date',
          default: new Date()
        },
        uploaded_by: {
          bsonType: 'objectId',
          description: 'Reference to users collection'
        }
      }
    }
  },
  indexes: [
    { 'uploaded_by': 1, 'upload_date': -1 },
    { 'file_name': 1 },
    { 'mime_type': 1 }
  ]
});

db.createCollection('processing_jobs', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['job_id', 'media_file', 'user', 'status', 'progress', 'created_at'],
      properties: {
        job_id: {
          bsonType: 'string',
          unique: true,
          description: 'Unique job identifier'
        },
        media_file: {
          bsonType: 'objectId',
          description: 'Reference to media_files collection'
        },
        user: {
          bsonType: 'objectId',
          description: 'Reference to users collection'
        },
        status: {
          bsonType: 'string',
          enum: ['pending', 'processing', 'completed', 'failed', 'cancelled']
        },
        progress: {
          bsonType: 'number',
          minimum: 0,
          maximum: 100
        },
        created_at: {
          bsonType: 'date',
          default: new Date()
        }
      }
    }
  },
  indexes: [
    { 'job_id': 1 },
    { 'user': 1 },
    { 'status': 1 },
    { 'created_at': 1 }
  ]
});

db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['email', 'username', 'password_hash', 'is_active', 'created_at'],
      properties: {
        email: {
          bsonType: 'string',
          unique: true,
          description: 'User email address'
        },
        username: {
          bsonType: 'string',
          unique: true,
          description: 'Unique username'
        },
        password_hash: {
          bsonType: 'string',
          description: 'Hashed password'
        },
        is_active: {
          bsonType: 'boolean',
          default: true
        },
        created_at: {
          bsonType: 'date',
          default: new Date()
        }
      }
    }
  },
  indexes: [
    { 'email': 1 },
    { 'username': 1 }
  ]
});

db.createCollection('transcription_results', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['job_id', 'media_file_id', 'full_text', 'language', 'confidence', 'segments', 'processing_time', 'created_at'],
      properties: {
        job_id: {
          bsonType: 'string',
          description: 'Reference to processing_jobs collection'
        },
        media_file_id: {
          bsonType: 'objectId',
          description: 'Reference to media_files collection'
        },
        full_text: {
          bsonType: 'string',
          description: 'Complete transcription text'
        },
        language: {
          bsonType: 'string',
          description: 'Detected language code'
        },
        confidence: {
          bsonType: 'number',
          minimum: 0,
          maximum: 1,
          description: 'Confidence score'
        },
        segments: [{
          type: 'array',
          items: {
            start_time: { bsonType: 'number' },
            end_time: { bsonType: 'number' },
            text: { bsonType: 'string' },
            confidence: { bsonType: 'number' }
          }
        }],
        processing_time: {
          bsonType: 'number',
          description: 'Processing time in milliseconds'
        },
        created_at: {
          bsonType: 'date',
          default: new Date()
        }
      }
    }
  },
  indexes: [
    { 'job_id': 1 },
    { 'media_file_id': 1 }
  ]
});

print('MongoDB initialized for ai_media_translation database');