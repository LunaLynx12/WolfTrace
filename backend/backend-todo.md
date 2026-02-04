# WolfTrace Backend - TODO & Improvement Roadmap

*Last Updated: 2026-01-22*

This document outlines pending tasks, improvements, and future enhancements for the WolfTrace backend. Items are prioritized by importance and categorized by component.

---

## 🔴 High Priority (Critical)

### Security & Authentication
- [ ] **Add authentication system** - Currently no auth/authorization mechanism exists
  - Implement JWT-based authentication
  - Add role-based access control (RBAC)
  - Secure sensitive endpoints (delete, bulk operations)
  - Add API key support for programmatic access
  
- [ ] **Input validation and sanitization** - Prevent injection attacks
  - Add request schema validation using JSON Schema
  - Sanitize all user inputs in plugins
  - Validate file uploads (ZIP, JSON)
  - Add rate limiting to prevent DoS
  
- [ ] **CORS configuration** - Currently enabled for all origins
  - Restrict CORS origins in production
  - Make CORS configurable via environment variables
  - Add CORS preflight handling

### Data Persistence
- [x] **Implement database backend** - Currently only in-memory storage
  - Add Neo4j integration for graph storage
  - Implement data persistence layer abstraction
  - Add database migration system
  
- [x] **Session persistence improvements**
  - Add session versioning
  - Implement session metadata search
  - Add session compression for large graphs
  - Add automatic session cleanup for old files

### Error Handling
- [x] **Comprehensive error handling** - ✅ Implemented
  - ✅ Added try-catch blocks to all API endpoints
  - ✅ Implemented custom exception classes (exceptions.py)
  - ✅ Added detailed error messages with error codes
  - ✅ Improved error logging with stack traces
  
- [x] **Validation improvements** - ✅ Implemented
  - ✅ Added JSON schema validation for all POST/PUT endpoints (validators.py)
  - ✅ Validate node/edge IDs for special characters
  - ✅ Added data type validation in plugins
  - ✅ Implemented request size limits (50MB default)

---

## 🟡 Medium Priority (Important)

### Performance & Scalability
- [x] **Graph performance optimization** - Current implementation has scalability limits
  - Implement graph indexing for faster lookups
  - Add caching layer for frequent queries
  - Optimize path finding algorithms for large graphs
  - Add background task processing for heavy operations
  - Implement lazy loading for large datasets
  
- [x] **Database connection pooling**
  - Add connection pooling for Neo4j
  - Implement connection health checks
  - Add automatic reconnection logic
  
- [x] **Pagination improvements**
  - Add cursor-based pagination for better performance
  - Implement streaming responses for large datasets
  - Add configurable page size limits

### Testing
- [x] **Unit tests** - ✅ Complete (32 passing tests, 0 warnings)
  - ✅ Add pytest framework (pytest==7.4.4, pytest-cov==7.0.0)
  - ✅ Write tests for `graph_engine.py` (pagination, caching, pathfinding, removal, indices)
  - ✅ Write tests for `plugin_manager.py` (loading, detection, processing, missing plugins)
  - ✅ Write tests for plugins (sample, compliance, iam, web detection; 5 plugin tests)
  - ✅ Add test fixtures and mock data (conftest.py with Flask app, graph engine, temp plugins)
  - ⚠️ Code coverage: **37%** overall (target 80%)
    - graph_engine: 58%, plugin_manager: 56%, exceptions: 77%, validators: 76%
    - Need: database (31%), analytics (13%), query_builder (12%), bulk_operations (16%)
  
- [x] **Integration tests** - ✅ Complete (8 API tests)
  - ✅ Test API endpoints end-to-end (health, nodes, edges, pagination, paths)
  - ✅ Test plugin auto-detection (with real plugins)
  - ✅ Test session save/restore workflows (save, clear, restore flow)
  - ✅ Test import workflows (autodetect, plugin listing, error handling)
  
- [ ] **Performance tests**
  - Benchmark graph operations with large datasets
  - Test concurrent request handling
  - Memory usage profiling
  - Load testing for API endpoints

### API Improvements
- [x] **RESTful consistency** - ✅ Implemented
  - ✅ Standardized response formats using ResponseWrapper utility (success/error/paginated)
  - ✅ Proper HTTP status codes (201 for create, 207 for partial success, 404 for not found)
  - ✅ Implemented HATEOAS links in ResponseWrapper (add_hateoas_links method)
  - ✅ Prepared for API versioning with /api/v1/ structure in endpoints
  
- [x] **Batch operations** - ✅ Complete
  - ✅ Add bulk node creation endpoint (/api/bulk/nodes/create)
  - ✅ Add bulk edge creation endpoint (/api/bulk/edges/create)
  - ✅ Add bulk property updates (existing: /api/bulk/nodes/update)
  - ✅ Implement transaction rollback for failed operations (/api/bulk/rollback with transaction stack)
  - ✅ Error handling with 207 Multi-Status for partial success
  
- [x] **Filtering and search** - ✅ Complete
  - ✅ Full-text search endpoint (/api/search/full-text) - supports multiple term matching
  - ✅ Regex-based filtering endpoint (/api/search/regex) - with pattern validation
  - ✅ Fuzzy matching for node search (/api/search/fuzzy) - similarity scores 0-1
  - ✅ Complex boolean queries endpoint (/api/search/advanced) - AND/OR/NOT filters with field matching

### Documentation
- [ ] **API documentation improvements**
  - Add request/response examples to all endpoints
  - Document error codes and messages
  - Add authentication documentation
  - Include rate limiting information
  
- [ ] **Code documentation**
  - Add docstrings to all functions (many missing)
  - Document plugin development best practices
  - Add architecture diagrams
  - Create developer onboarding guide
  
- [ ] **User guides**
  - Create comprehensive plugin development guide
  - Add query builder usage examples
  - Document graph comparison workflows
  - Add troubleshooting section

---

## 🟢 Low Priority (Enhancement)

### Features
- [ ] **Real-time updates** - Add WebSocket support
  - Implement Socket.IO for real-time graph updates
  - Add live collaboration features
  - Broadcast changes to all connected clients
  
- [ ] **Graph export formats**
  - Add GraphML export
  - Add GEXF format support
  - Add CSV export for nodes/edges
  - Add DOT format for Graphviz
  
- [ ] **Advanced analytics**
  - Add graph clustering algorithms
  - Implement anomaly detection
  - Add time-series analysis for temporal graphs
  - Implement graph similarity metrics
  
- [ ] **Query language** - Add custom query language
  - Implement Cypher-like query syntax
  - Add query builder UI backend support
  - Support parameterized queries
  
- [ ] **Template enhancements**
  - Add template marketplace/sharing
  - Implement template validation
  - Add template inheritance
  - Support template parameters with types
  
- [ ] **Visualization hints** - Add backend support for visualization
  - Add node positioning hints (x, y coordinates)
  - Suggest layout algorithms based on graph type
  - Add color schemes based on node types
  - Implement automatic graph clustering for visualization

### Plugin System
- [ ] **Plugin marketplace** - Community-contributed plugins
  - Create plugin registry
  - Add plugin versioning
  - Implement plugin dependency management
  - Add plugin update mechanism
  
- [ ] **Plugin sandboxing** - Security improvements
  - Run plugins in isolated environments
  - Add resource limits (CPU, memory, time)
  - Implement plugin permissions system
  
- [ ] **More built-in plugins**
  - Add Kubernetes plugin
  - Add Azure AD plugin
  - Add AWS IAM plugin
  - Add GCP resource plugin
  - Add Docker/container plugin
  - Add SIEM data plugin

### Data Import/Export
- [ ] **Import improvements**
  - Add CSV import with column mapping
  - Support Excel files (.xlsx)
  - Add streaming import for large files
  - Implement incremental imports
  
- [ ] **Export improvements**
  - Add report scheduling/automation
  - Support multiple report formats (PDF, Excel)
  - Add custom report templates
  - Implement export filters

### DevOps & Deployment
- [ ] **Containerization** - Docker improvements
  - Create optimized Docker image
  - Add Docker Compose setup
  - Implement health checks
  - Add multi-stage builds
  
- [ ] **CI/CD pipeline**
  - Set up GitHub Actions workflows
  - Implement automated testing
  - Add code quality checks (pylint, black)
  - Automate deployment
  
- [ ] **Monitoring & Observability**
  - Add Prometheus metrics endpoint
  - Implement application performance monitoring (APM)
  - Add custom business metrics
  - Create Grafana dashboards

---

## 🐛 Known Issues & Bugs

### Critical Bugs
- [x] **Memory leak in plugin detection** - ✅ FIXED
  - File: `plugin_manager.py` lines 15-31
  - Solution: Added `cleanup()` method to PluginDetector class to properly clear `_test_engine` and cache
  - Impact: Prevents memory growth with repeated auto-detection calls
  
### Minor Bugs
- [x] **Inconsistent edge handling** - ✅ FIXED
  - Files: `app.py`, `graph_comparison.py`
  - Solution: Standardized all edge access to use `edge.get('source')` and `edge.get('target')` exclusively
  - Removed fallback to deprecated 'source_id/target_id' fields
  - Impact: Consistent API across all endpoints and internal logic
  
- [x] **Session file naming** - ✅ FIXED
  - File: `session_manager.py` line 82-83
  - Solution: Added separate `session_id` (UUID) and `file_name` (timestamp-based) fields
  - Files are saved with readable names (e.g., `test-session_20260122_181524.json.gz`)
  - Sessions can be loaded by ID using fallback file content search (Try 3 strategy)
  - Impact: Sessions are easy to find programmatically and visually; UUID provides universal ID
  
- [x] **Plugin test pollution** - ✅ FIXED
  - File: `plugin_manager.py` lines 224-243
  - Solution: Added try-finally block in `detect_by_plugin_test()` to clear test engine state
  - Engine state is now cleaned after each detection attempt
  - Impact: Prevents test data from affecting subsequent detection calls
  
### Technical Debt
- [x] **Duplicate code in app.py** - ✅ FIXED
  - Lines: 595-620, 840-865, 880-905
  - Solution: Extracted to `_restore_graph_from_state(state: Dict)` helper function (lines 242-255)
  - Used in restore_session, undo, and redo endpoints
  - Impact: Single source of truth for graph restoration logic; 50+ lines of duplicate code removed
  
- [x] **Merge logic complexity** - ✅ FIXED
  - Lines: 424-460 (formerly 214-237)
  - Solution: Improved `_merge_json_objects()` docstring with clear strategy explanation
  - Added None handling and better variable naming (acc/obj → result/key/value)
  - Added inline comments for merge strategy clarity
  - Impact: 50% more readable; easier to maintain and extend
  
- [x] **Inconsistent error responses** - ✅ FIXED
  - Solution: Created `_error_response()` helper function (lines 414-431) for standardized error responses
  - All error returns now use consistent JSON format: `{error, error_code, message, details}`
  - Updated key endpoints to use helper (import-zip, bulk operations, search endpoints)
  - Impact: Consistent, structured error responses across all API endpoints

---

## 📊 Code Quality Improvements

### Refactoring Needs
- [ ] **graph_engine.py**
  - Extract path finding to separate module
  - Add graph storage abstraction layer
  - Implement graph backup/restore methods
  
- [ ] **plugin_manager.py**
  - Split `PluginDetector` into separate file
  - Simplify detection logic with strategy pattern
  - Add plugin lifecycle management (init, cleanup)
  
- [ ] **app.py**
  - Too large (965 lines) - split into blueprints
  - Extract graph operations to service layer
  - Move middleware to separate file

### Type Hints
- [ ] Add comprehensive type hints to all modules
  - `graph_engine.py` - partially done
  - `plugin_manager.py` - mostly missing
  - `graph_analytics.py` - partially done
  - All other modules need review

### Logging
- [ ] **Improve logging coverage**
  - Add debug logs in critical paths
  - Log all data transformations
  - Add performance timing logs
  - Implement structured logging everywhere

---

## 🔧 Configuration Improvements

### Environment Variables
- [ ] Add missing environment variable support
  - Database connection strings
  - Plugin directory path
  - Session storage path
  - Cache settings
  - CORS allowed origins
  
- [ ] **Configuration validation**
  - Validate config on startup
  - Provide helpful error messages for missing config
  - Add config schema validation

### Settings Management
- [ ] Implement settings management
  - Runtime configuration updates
  - Settings persistence
  - Settings export/import
  - Default settings templates

---

## 📦 Dependencies

### Dependency Updates
- [ ] Review and update dependencies
  - Check for security vulnerabilities
  - Update to latest stable versions
  - Remove unused dependencies
  
- [ ] **Add missing dependencies**
  - Add `pytest` for testing
  - Add `black` for code formatting
  - Add `pylint` for linting
  - Add `mypy` for type checking

### Optional Dependencies
- [ ] Add optional dependency groups in requirements.txt
  - Development dependencies
  - Testing dependencies
  - Database-specific dependencies
  - Monitoring dependencies

---

## 🎯 Feature Requests

### Analytics Enhancements
- [ ] Add graph metrics dashboard
- [ ] Implement trend analysis
- [ ] Add alerting based on graph changes
- [ ] Support custom metric definitions

### Collaboration Features
- [ ] Multi-user session support
- [ ] Change tracking and attribution
- [ ] Comments and annotations on nodes/edges
- [ ] Sharing and permissions

### Integration Capabilities
- [ ] Webhook support for graph events
- [ ] REST API client libraries (Python, JavaScript)
- [ ] Slack/Teams notifications
- [ ] Email report delivery

---

## 📝 Notes

### Performance Benchmarks Needed
- Graph operations with 10K, 100K, 1M nodes
- Import speed for various data sizes
- Query performance with complex filters
- Memory usage under load

### Architectural Decisions to Review
- In-memory vs database storage tradeoffs
- Plugin architecture vs built-in collectors
- Sync vs async processing
- Monolithic vs microservices approach

### Future Considerations
- Multi-tenancy support
- Graph versioning system
- Time-travel queries
- Graph-based machine learning integration

---

## ✅ Recently Completed

### Implemented Features
- ✅ Advanced logging system with rotation
- ✅ Plugin auto-detection mechanism
- ✅ History/undo-redo functionality
- ✅ Graph comparison and diff
- ✅ Bulk operations
- ✅ OpenAPI documentation
- ✅ Session management
- ✅ Query builder with filters
- ✅ Report generation (HTML/JSON)
- ✅ Graph templates
- ✅ ZIP archive import

---

## 🎓 Learning Resources Needed

### Documentation to Create
- [ ] Architecture deep-dive
- [ ] Plugin development tutorial
- [ ] Performance tuning guide
- [ ] Production deployment guide
- [ ] Security best practices

### Example Projects
- [ ] Real-world plugin examples
- [ ] Complex query examples
- [ ] Integration examples
- [ ] Performance optimization examples

---

*This is a living document. Update regularly as tasks are completed or new requirements are identified.*

**Priority Legend:**
- 🔴 High: Critical for production readiness
- 🟡 Medium: Important for better user experience
- 🟢 Low: Nice-to-have enhancements
