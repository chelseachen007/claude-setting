# GitHub Search Strategies

## Search Query Patterns by Task Type

### CLI Tools
```bash
# For command-line interface tools
"<task> cli tool" language:python
"<task> command line" language:go
"<task> shell" language:bash
```

### Libraries and SDKs
```bash
# For libraries
"<task> library" language:javascript
"<task> sdk" language:python
"<task> api client"
```

### Framework-Specific
```bash
# Web frameworks
"<task> react" language:typescript
"<task> vue" language:javascript
"<task> next.js"
```

### Data Processing
```bash
# For data tasks
"<task> parser" language:python
"<task> converter" language:javascript
"<task> etl"
```

### Automation
```bash
# For automation tasks
"<task> automation" language:python
"<task> workflow"
"<task> scheduler"
```

### File Processing
```bash
# For file operations
"<file-type> parser" language:python
"<file-type> generator"
"<file-type> converter"
```

## Filtering by Quality

### Star Count Filters
```bash
# Using GitHub search syntax
"<query>" stars:>1000
"<query>" stars:>5000 language:python
```

### Recently Updated
```bash
# Find active projects
"<query>" pushed:>2024-01-01
```

### License Filter
```bash
# Permissive licenses only
"<query>" license:mit OR license:apache-2.0
```

## Language-Specific Patterns

| Language | Query Pattern |
|----------|---------------|
| Python | `"<task>" language:python` |
| JavaScript/TypeScript | `"<task>" language:typescript OR language:javascript` |
| Go | `"<task>" language:go` |
| Rust | `"<task>" language:rust` |
| Java | `"<task>" language:java` |
| Ruby | `"<task>" language:ruby` |
