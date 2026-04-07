"""
Comprehensive test suite for Graph Primitives:
- Node Creation
- Edge Creation
- Directed Graph Representation
- Node Labeling
"""

import json
import sys
from pathlib import Path
from typing import Any

import networkx as nx

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.graph_builder import (
    GraphEdge,
    GraphNode,
    SystemGraph,
    build_system_graph,
    build_graph,
)


def test_node_creation() -> dict[str, Any]:
    """Test that nodes can be created with proper structure."""
    print("\n=== TEST 1: Node Creation ===")
    try:
        # Test GraphNode dataclass
        node1 = GraphNode(id="file:test.py", node_type="file", label="test.py", file_path="test.py")
        node2 = GraphNode(id="class:MyClass", node_type="class", label="MyClass")
        node3 = GraphNode(id="function:foo", node_type="function", label="foo")
        node4 = GraphNode(id="module:os", node_type="module", label="os")

        nodes = [node1, node2, node3, node4]
        
        print(f"✅ Created {len(nodes)} nodes successfully")
        print(f"   - File node: {node1}")
        print(f"   - Class node: {node2}")
        print(f"   - Function node: {node3}")
        print(f"   - Module node: {node4}")

        # Verify node structure
        assert node1.id == "file:test.py", "File node ID mismatch"
        assert node1.node_type == "file", "File node type mismatch"
        assert node1.label == "test.py", "File node label mismatch"
        assert node2.label == "MyClass", "Class node label mismatch"

        print("✅ All node structure validations passed")
        
        return {
            "status": "PASS",
            "nodes_created": len(nodes),
            "node_types": ["file", "class", "function", "module"],
        }
    except Exception as e:
        print(f"❌ Node creation failed: {e}")
        return {"status": "FAIL", "error": str(e)}


def test_edge_creation() -> dict[str, Any]:
    """Test that edges can be created with proper structure."""
    print("\n=== TEST 2: Edge Creation ===")
    try:
        # Test GraphEdge dataclass
        edge1 = GraphEdge(source="file:test.py", target="class:MyClass", edge_type="contains")
        edge2 = GraphEdge(source="class:MyClass", target="function:foo", edge_type="contains")
        edge3 = GraphEdge(source="function:foo", target="function:bar", edge_type="calls")
        edge4 = GraphEdge(source="file:test.py", target="module:os", edge_type="imports")

        edges = [edge1, edge2, edge3, edge4]

        print(f"✅ Created {len(edges)} edges successfully")
        print(f"   - Contains edge (file->class): {edge1}")
        print(f"   - Contains edge (class->function): {edge2}")
        print(f"   - Calls edge (function->function): {edge3}")
        print(f"   - Imports edge (file->module): {edge4}")

        # Verify edge structure
        assert edge1.source == "file:test.py", "Edge source mismatch"
        assert edge1.target == "class:MyClass", "Edge target mismatch"
        assert edge1.edge_type == "contains", "Edge type mismatch"
        assert edge3.edge_type == "calls", "Calls edge type mismatch"
        assert edge4.edge_type == "imports", "Imports edge type mismatch"

        print("✅ All edge structure validations passed")
        
        return {
            "status": "PASS",
            "edges_created": len(edges),
            "edge_types": ["contains", "calls", "imports"],
        }
    except Exception as e:
        print(f"❌ Edge creation failed: {e}")
        return {"status": "FAIL", "error": str(e)}


def test_directed_graph() -> dict[str, Any]:
    """Test that directed graph is properly constructed."""
    print("\n=== TEST 3: Directed Graph Representation ===")
    try:
        # Create a simple directed graph using NetworkX
        graph = nx.DiGraph()
        
        # Add nodes
        graph.add_node("file:test.py", type="file")
        graph.add_node("class:MyClass", type="class")
        graph.add_node("function:foo", type="function")
        graph.add_node("function:bar", type="function")
        graph.add_node("module:os", type="module")

        # Add edges
        graph.add_edge("file:test.py", "class:MyClass", relation="contains")
        graph.add_edge("class:MyClass", "function:foo", relation="contains")
        graph.add_edge("function:foo", "function:bar", relation="calls")
        graph.add_edge("file:test.py", "module:os", relation="imports")

        # Verify it's directed
        assert isinstance(graph, nx.DiGraph), "Graph is not a DiGraph"
        assert graph.number_of_nodes() == 5, f"Expected 5 nodes, got {graph.number_of_nodes()}"
        assert graph.number_of_edges() == 4, f"Expected 4 edges, got {graph.number_of_edges()}"

        # Verify directionality - reverse edges should NOT exist
        assert not graph.has_edge("class:MyClass", "file:test.py"), "Graph is not directed (reverse edge exists)"
        
        # Verify forward edges exist
        assert graph.has_edge("file:test.py", "class:MyClass"), "Forward edge missing"
        assert graph.has_edge("function:foo", "function:bar"), "Call edge missing"

        print(f"✅ Directed graph created successfully")
        print(f"   - Nodes: {graph.number_of_nodes()}")
        print(f"   - Edges: {graph.number_of_edges()}")
        print(f"   - Is DiGraph: {isinstance(graph, nx.DiGraph)}")
        print(f"   - Forward edges verified: ✅")
        print(f"   - No reverse edges: ✅")

        return {
            "status": "PASS",
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "is_directed": isinstance(graph, nx.DiGraph),
        }
    except Exception as e:
        print(f"❌ Directed graph test failed: {e}")
        return {"status": "FAIL", "error": str(e)}


def test_node_labeling() -> dict[str, Any]:
    """Test that nodes have proper labeling."""
    print("\n=== TEST 4: Node Labeling ===")
    try:
        nodes = [
            GraphNode(id="file:path/to/test.py", node_type="file", label="test.py", file_path="path/to/test.py"),
            GraphNode(id="class:path/to/test.py:MyClass", node_type="class", label="MyClass", file_path="path/to/test.py"),
            GraphNode(id="function:path/to/test.py:foo", node_type="function", label="foo", file_path="path/to/test.py"),
            GraphNode(id="module:os", node_type="module", label="os"),
        ]

        # Test labels are human-readable
        assert nodes[0].label == "test.py", "File label not human-readable"
        assert nodes[1].label == "MyClass", "Class label not human-readable"
        assert nodes[2].label == "foo", "Function label not human-readable"
        assert nodes[3].label == "os", "Module label not human-readable"

        # Test IDs are unique and qualified
        ids = [n.id for n in nodes]
        assert len(ids) == len(set(ids)), "Duplicate node IDs"

        # Test structure
        for node in nodes:
            assert ":" in node.id or node.node_type == "module", "Node ID not properly qualified"
            assert node.label, "Node label is empty"
            assert node.node_type in ["file", "class", "function", "module"], "Invalid node type"

        print(f"✅ Node labeling validated for {len(nodes)} nodes")
        print(f"   - File: label='test.py', id qualified with path")
        print(f"   - Class: label='MyClass', id qualified with class name")
        print(f"   - Function: label='foo', id qualified with function name")
        print(f"   - Module: label='os', id='module:os'")
        print(f"   - All IDs unique: ✅")
        print(f"   - All labels human-readable: ✅")

        return {
            "status": "PASS",
            "nodes_labeled": len(nodes),
            "id_qualification": "qualified with context",
            "label_format": "human-readable",
        }
    except Exception as e:
        print(f"❌ Node labeling test failed: {e}")
        return {"status": "FAIL", "error": str(e)}


def test_build_graph_from_ast() -> dict[str, Any]:
    """Test build_graph function with sample AST data."""
    print("\n=== TEST 5: Build Graph from AST Data ===")
    try:
        # Sample AST data
        ast_data = [
            {
                "file": "main.py",
                "data": {
                    "functions": [
                        {"name": "process_data", "calls": [{"called_name": "parse"}, {"called_name": "validate"}]},
                        {"name": "parse", "calls": []},
                    ],
                    "classes": [{"name": "DataProcessor"}],
                    "imports": ["os", "json"],
                }
            }
        ]

        graph, call_info = build_graph(ast_data)

        # Verify graph properties
        assert isinstance(graph, nx.DiGraph), "Graph is not DiGraph"
        assert graph.number_of_nodes() > 0, "Graph has no nodes"
        assert graph.number_of_edges() > 0, "Graph has no edges"

        nodes_by_type = {}
        for node, data in graph.nodes(data=True):
            node_type = data.get("type", "unknown")
            nodes_by_type[node_type] = nodes_by_type.get(node_type, 0) + 1

        print(f"✅ Graph built from AST data successfully")
        print(f"   - Total nodes: {graph.number_of_nodes()}")
        print(f"   - Total edges: {graph.number_of_edges()}")
        print(f"   - Nodes by type: {nodes_by_type}")
        print(f"   - Call edges tracked: {call_info.get('call_edges', 0)}")

        return {
            "status": "PASS",
            "total_nodes": graph.number_of_nodes(),
            "total_edges": graph.number_of_edges(),
            "nodes_by_type": nodes_by_type,
            "call_edges": call_info.get("call_edges", 0),
        }
    except Exception as e:
        print(f"❌ Build graph from AST failed: {e}")
        return {"status": "FAIL", "error": str(e)}


def test_system_graph_with_real_files() -> dict[str, Any]:
    """Test building a system graph from actual source files."""
    print("\n=== TEST 6: System Graph from Real Files ===")
    try:
        # Use backend app directory
        test_path = Path(__file__).parent.parent / "app"
        
        if not test_path.exists():
            print(f"⚠️  Test path not found: {test_path}")
            return {"status": "SKIP", "reason": "Test path not found"}

        result = build_system_graph(str(test_path), max_files=50)

        # Verify result structure
        assert isinstance(result, dict), "Result is not a dict"
        assert "root" in result, "Missing 'root' key"
        assert "nodes" in result, "Missing 'nodes' key"
        assert "edges" in result, "Missing 'edges' key"
        assert "summary" in result, "Missing 'summary' key"

        nodes = result.get("nodes", [])
        edges = result.get("edges", [])
        summary = result.get("summary", {})

        # Verify nodes have required fields
        for node in nodes[:3]:  # Check first 3 nodes
            assert "id" in node, "Node missing 'id'"
            assert "node_type" in node, "Node missing 'node_type'"
            assert "label" in node, "Node missing 'label'"

        # Verify edges have required fields
        for edge in edges[:3]:  # Check first 3 edges
            assert "source" in edge, "Edge missing 'source'"
            assert "target" in edge, "Edge missing 'target'"
            assert "edge_type" in edge, "Edge missing 'edge_type'"

        print(f"✅ System graph built successfully from real files")
        print(f"   - Root: {result.get('root')}")
        print(f"   - Total nodes: {len(nodes)}")
        print(f"   - Total edges: {len(edges)}")
        print(f"   - Files scanned: {summary.get('files_scanned', 'N/A')}")
        print(f"   - Summary: {json.dumps(summary, indent=6)}")

        return {
            "status": "PASS",
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "files_scanned": summary.get("files_scanned", 0),
            "summary": summary,
        }
    except Exception as e:
        print(f"❌ System graph test failed: {e}")
        return {"status": "FAIL", "error": str(e)}


def main():
    """Run all graph primitive tests."""
    print("=" * 60)
    print("GRAPH PRIMITIVES COMPREHENSIVE TEST SUITE")
    print("=" * 60)

    results = {
        "Node Creation": test_node_creation(),
        "Edge Creation": test_edge_creation(),
        "Directed Graph": test_directed_graph(),
        "Node Labeling": test_node_labeling(),
        "Build Graph from AST": test_build_graph_from_ast(),
        "System Graph from Files": test_system_graph_with_real_files(),
    }

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total_tests = len(results)
    passed = sum(1 for r in results.values() if r.get("status") == "PASS")
    failed = sum(1 for r in results.values() if r.get("status") == "FAIL")
    skipped = sum(1 for r in results.values() if r.get("status") == "SKIP")

    for test_name, result in results.items():
        status_emoji = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⏭️"
        print(f"{status_emoji} {test_name}: {result['status']}")
        if result["status"] == "FAIL":
            print(f"   Error: {result.get('error', 'Unknown error')}")

    print("\n" + "-" * 60)
    print(f"Total: {total_tests} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
    print("-" * 60)

    # Final status
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {failed} TEST(S) FAILED")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
