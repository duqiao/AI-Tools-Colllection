# API Contracts: Mini-Program Media Translation Tool

This directory contains detailed API specifications for the uni-app to FastAPI integration, ensuring seamless communication between the cross-platform frontend and Python backend.

## Contract Files

### [authentication-api.md](authentication-api.md)
User authentication and session management APIs with WeChat integration.

### [translation-api.md](translation-api.md)  
Media file upload, processing, and transcription APIs.

### [user-management-api.md](user-management-api.md)
User profile, preferences, and account management APIs.

### [subscription-api.md](subscription-api.md)
VIP subscription plans, payments, and quota management APIs.

### [system-api.md](system-api.md)
System configuration, settings, and administrative APIs.

## API Design Principles

### 1. Backward Compatibility
- All existing API endpoints must maintain identical request/response formats
- Response structure and status codes must remain unchanged
- Error handling must preserve existing behavior

### 2. RESTful Design
- Use HTTP methods appropriately (GET, POST, PUT, DELETE)
- Implement proper status codes for different scenarios
- Support both JSON and form-data responses

### 3. Security Standards
- JWT-based authentication for all protected endpoints
- API rate limiting to prevent abuse
- Input validation and sanitization

### 4. Performance Requirements
- Response times under 200ms for non-media requests
- Support for high concurrency (1000+ requests)
- Efficient file upload with progress tracking

## Versioning Strategy

### Current Version: v1.0
- Maintains full compatibility with existing WeChat mini-program
- Response format: JSON with consistent structure
- Error handling: Standardized error response format

### Future Versions
- Versioning through URL path (/api/v1/, /api/v2/)
- Backward compatibility maintained for at least one major version
- Deprecation notices for breaking changes

## Testing Requirements

### Contract Testing
- Each API contract must have comprehensive test coverage
- Test both success and error scenarios
- Validate response formats and status codes

### Integration Testing
- Test complete workflows from uni-app to FastAPI
- Validate file upload and processing pipelines
- Test authentication and authorization flows

## Documentation Standards

Each API contract includes:
- Detailed endpoint descriptions
- Request/response examples
- Error scenarios and handling
- Authentication requirements
- Rate limiting information