# Knowledge Graph with Memgraph

## Overview

The coding agent uses Memgraph, a high-performance graph database, to build and query a knowledge graph of your codebase structure. This enables the agent to understand code relationships, navigate dependencies, and provide intelligent insights.

## What is a Knowledge Graph?

A knowledge graph represents your code as nodes (files, classes, functions) and relationships (imports, calls, inherits). This structure allows for powerful queries like:

- "Find all places where function X is called"
- "Show me the class hierarchy"
- "Detect circular imports"
- "Get the call graph for this function"

## Graph Schema

### Nodes

#### FileNode

Represents a source code file.

```cypher
(:FileNode {
  path: string,           // Relative path
  name: string,           // Filename
  language: string,       // Programming language
  lines_of_code: int,     // LOC count
  last_modified: string   // Timestamp
})
```

#### ClassNode

Represents a class definition.

```cypher
(:ClassNode {
  name: string,           // Class name
  line_start: int,        // Starting line number
  line_end: int,          // Ending line number
  docstring: string,      // Class docstring
  is_abstract: boolean    // Is abstract class
})
```

#### FunctionNode

Represents a function or method.

```cypher
(:FunctionNode {
  name: string,           // Function name
  parameters: string,     // JSON of parameters
  return_type: string,    // Return type annotation
  line_start: int,        // Starting line
  line_end: int,          // Ending line
  docstring: string,      // Function docstring
  is_async: boolean,      // Is async function
  is_method: boolean      // Is class method
})
```

#### ModuleNode

Represents an imported module.

```cypher
(:ModuleNode {
  name: string,           // Module name
  is_stdlib: boolean      // Is standard library
})
```

### Relationships

#### CONTAINS

File contains class or function.

```cypher
(:FileNode)-[:CONTAINS]->(:ClassNode)
(:FileNode)-[:CONTAINS]->(:FunctionNode)
```

#### HAS_METHOD

Class has method.

```cypher
(:ClassNode)-[:HAS_METHOD]->(:FunctionNode)
```

#### INHERITS_FROM

Class inherits from another class.

```cypher
(:ClassNode)-[:INHERITS_FROM]->(:ClassNode)
```

#### CALLS

Function calls another function.

```cypher
(:FunctionNode)-[:CALLS {call_count: int}]->(:FunctionNode)
```

#### IMPORTS

File imports module.

```cypher
(:FileNode)-[:IMPORTS {import_type: string, alias: string}]->(:ModuleNode)
```

## Building the Graph

### Via CLI

```bash
python -m src.cli_enhanced run "Build knowledge graph for this project" --user-id admin
```

### Via API

```bash
curl -X POST http://localhost:8000/api/v1/graph/build \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "/path/to/project",
    "file_extensions": [".py"]
  }'
```

### Via Python

```python
from src.middleware.knowledge_graph import knowledge_graph

# Build graph
stats = knowledge_graph.build_graph_from_directory(
    directory="/path/to/project",
    file_extensions=[".py"],
    exclude_patterns=["__pycache__", ".venv", "node_modules"]
)

print(f"Built graph with {stats['files']} files, {stats['classes']} classes")
```

## Querying the Graph

### Find Function Usages

```python
from src.middleware.knowledge_graph import knowledge_graph

# Find where a function is called
usages = knowledge_graph.find_function_usages("process_data")

for usage in usages:
    print(f"{usage['caller']} calls {usage['callee']} {usage['count']} times")
```

**Cypher Query:**

```cypher
MATCH (caller:FunctionNode)-[r:CALLS]->(callee:FunctionNode {name: 'process_data'})
RETURN caller.name, callee.name, r.call_count
```

### Get Class Hierarchy

```python
# Get inheritance chain
hierarchy = knowledge_graph.get_class_hierarchy("MyClass")

print(f"Class {hierarchy['class']} inherits from:")
for base in hierarchy['bases']:
    print(f"  - {base}")
```

**Cypher Query:**

```cypher
MATCH path = (c:ClassNode {name: 'MyClass'})-[:INHERITS_FROM*]->(base:ClassNode)
RETURN c.name, collect(base.name) as bases
```

### Analyze Dependencies

```python
# Get all imports for a file
deps = knowledge_graph.get_file_dependencies("src/main.py")

for dep in deps:
    print(f"{dep['module']} ({dep['type']})")
```

**Cypher Query:**

```cypher
MATCH (f:FileNode {path: 'src/main.py'})-[r:IMPORTS]->(m:ModuleNode)
RETURN m.name, r.import_type, r.alias, m.is_stdlib
```

### Detect Circular Imports

```python
# Find circular import chains
cycles = knowledge_graph.find_circular_imports()

for cycle in cycles:
    print("Circular import detected:")
    for file in cycle['cycle']:
        print(f"  → {file}")
```

**Cypher Query:**

```cypher
MATCH path = (f1:FileNode)-[:IMPORTS*2..]->(f2:FileNode)-[:IMPORTS]->(f1)
RETURN [n in nodes(path) | n.path] as cycle
LIMIT 10
```

### Get Call Graph

```python
# Get function call chain
call_graph = knowledge_graph.get_function_call_graph("main", depth=3)

for call in call_graph['calls']:
    chain = " → ".join(call['call_chain'])
    print(chain)
```

**Cypher Query:**

```cypher
MATCH path = (f:FunctionNode {name: 'main'})-[:CALLS*1..3]->(called:FunctionNode)
RETURN [n in nodes(path) | n.name] as call_chain
```

## Agent Tools

The agent has access to these knowledge graph tools:

### `build_code_knowledge_graph`

Build graph for a project directory.

### `find_function_usages`

Find all places where a function is called.

### `get_class_hierarchy`

Get inheritance hierarchy for a class.

### `analyze_file_dependencies`

Get all dependencies for a file.

### `find_circular_imports`

Detect circular import issues.

### `get_function_call_graph`

Get call graph showing function call chains.

### `get_knowledge_graph_stats`

Get statistics about the graph.

## Example Queries

### Find All Classes in a File

```cypher
MATCH (f:FileNode {path: 'src/models.py'})-[:CONTAINS]->(c:ClassNode)
RETURN c.name, c.line_start, c.line_end
```

### Find All Methods of a Class

```cypher
MATCH (c:ClassNode {name: 'UserModel'})-[:HAS_METHOD]->(m:FunctionNode)
RETURN m.name, m.parameters, m.return_type
```

### Find Most Called Functions

```cypher
MATCH (caller:FunctionNode)-[r:CALLS]->(callee:FunctionNode)
RETURN callee.name, sum(r.call_count) as total_calls
ORDER BY total_calls DESC
LIMIT 10
```

### Find Files with Most Dependencies

```cypher
MATCH (f:FileNode)-[:IMPORTS]->(m:ModuleNode)
WITH f, count(m) as dep_count
RETURN f.path, dep_count
ORDER BY dep_count DESC
LIMIT 10
```

### Find Unused Functions

```cypher
MATCH (f:FunctionNode)
WHERE NOT (f)<-[:CALLS]-()
  AND NOT (f)<-[:HAS_METHOD]-()
RETURN f.name, f.line_start
```

## Memgraph Lab UI

Access the visual interface at `http://localhost:3000`

### Visualize Graph

```cypher
// Show all nodes and relationships (limit for large graphs)
MATCH (n)
OPTIONAL MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 100
```

### Explore Specific File

```cypher
MATCH path = (f:FileNode {name: 'main.py'})-[*1..2]-(related)
RETURN path
```

## Performance Tips

1. **Index Important Properties**
   - File paths, class names, function names are already indexed

2. **Limit Query Depth**
   - Use `LIMIT` clause for large graphs
   - Specify maximum path length in relationship patterns

3. **Incremental Updates**
   - Rebuild only changed files instead of entire project

4. **Query Optimization**
   - Use specific node labels
   - Filter early in the query
   - Use `EXPLAIN` to analyze query plans

## Integration with Agent

The agent automatically uses the knowledge graph when:

1. **Code Navigation**: Finding definitions, usages, references
2. **Refactoring**: Understanding impact of changes
3. **Bug Detection**: Analyzing call chains and dependencies
4. **Documentation**: Generating architecture diagrams
5. **Code Review**: Identifying code smells and patterns

## Advanced Use Cases

### Generate Architecture Diagram

````python
# Get all classes and their relationships
query = """
MATCH (c1:ClassNode)-[:INHERITS_FROM]->(c2:ClassNode)
RETURN c1.name, c2.name
"""

results = knowledge_graph.db.execute_and_fetch(query)

# Generate mermaid diagram
print("```mermaid")
print("classDiagram")
for r in results:
    print(f"  {r['c2.name']} <|-- {r['c1.name']}")
print("```")
````

### Find Code Duplication

```python
# Find functions with similar names (potential duplicates)
query = """
MATCH (f1:FunctionNode), (f2:FunctionNode)
WHERE f1.name CONTAINS 'process' AND f2.name CONTAINS 'process'
  AND id(f1) < id(f2)
RETURN f1.name, f2.name
"""
```

### Analyze Test Coverage

```python
# Find functions without test coverage
query = """
MATCH (f:FunctionNode)
WHERE NOT EXISTS {
  MATCH (test:FunctionNode)
  WHERE test.name STARTS WITH 'test_' AND test.name CONTAINS f.name
}
RETURN f.name
```

## Troubleshooting

### Connection Issues

```python
# Test connection
from src.middleware.knowledge_graph import knowledge_graph

try:
    stats = knowledge_graph.get_graph_stats()
    print("Connected successfully!")
except Exception as e:
    print(f"Connection failed: {e}")
```

### Clear Graph

```python
# Clear all data
knowledge_graph.clear_graph()
```

### Rebuild Graph

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/graph/build \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"project_path": "."}'
```

## Resources

- [Memgraph Documentation](https://memgraph.com/docs)
- [Cypher Query Language](https://memgraph.com/docs/cypher-manual)
- [GQLAlchemy OGM](https://memgraph.github.io/gqlalchemy/)
- [Memgraph Lab](https://memgraph.com/docs/memgraph-lab)
