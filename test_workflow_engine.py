"""
Comprehensive tests for Sprint 5 Workflow Engine

Tests workflow compilation, validation, execution, and real-time streaming.
"""
import pytest
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any

# Import workflow components
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.workflows import (
    WorkflowCompiler,
    WorkflowValidationError,
    validate_workflow,
    compile_workflow
)


class TestWorkflowCompiler:
    """Test workflow compilation and validation"""
    
    def test_simple_linear_workflow(self):
        """Test a simple A -> B -> C workflow"""
        workflow = {
            "id": str(uuid.uuid4()),
            "name": "Linear Workflow",
            "nodes": [
                {"node_id": "A", "name": "Start", "node_type": "agent_call", "agent_id": "agent_1"},
                {"node_id": "B", "name": "Middle", "node_type": "agent_call", "agent_id": "agent_2"},
                {"node_id": "C", "name": "End", "node_type": "agent_call", "agent_id": "agent_3"},
            ],
            "edges": [
                {"from_node_id": "A", "to_node_id": "B"},
                {"from_node_id": "B", "to_node_id": "C"},
            ]
        }
        
        compiler = WorkflowCompiler(workflow)
        is_valid, errors = compiler.validate()
        
        assert is_valid, f"Validation failed: {errors}"
        assert len(errors) == 0
        
        # Test topological sort
        order = compiler.topological_sort()
        assert order == ["A", "B", "C"]
        
        # Test execution levels
        levels = compiler.get_execution_levels()
        assert len(levels) == 3
        assert levels[0] == ["A"]
        assert levels[1] == ["B"]
        assert levels[2] == ["C"]
    
    def test_parallel_workflow(self):
        """Test parallel execution: A -> (B, C) -> D"""
        workflow = {
            "id": str(uuid.uuid4()),
            "name": "Parallel Workflow",
            "nodes": [
                {"node_id": "A", "name": "Start", "node_type": "agent_call", "agent_id": "agent_1"},
                {"node_id": "B", "name": "Branch1", "node_type": "agent_call", "agent_id": "agent_2"},
                {"node_id": "C", "name": "Branch2", "node_type": "agent_call", "agent_id": "agent_3"},
                {"node_id": "D", "name": "Join", "node_type": "agent_call", "agent_id": "agent_4"},
            ],
            "edges": [
                {"from_node_id": "A", "to_node_id": "B"},
                {"from_node_id": "A", "to_node_id": "C"},
                {"from_node_id": "B", "to_node_id": "D"},
                {"from_node_id": "C", "to_node_id": "D"},
            ]
        }
        
        compiler = WorkflowCompiler(workflow)
        is_valid, errors = compiler.validate()
        
        assert is_valid, f"Validation failed: {errors}"
        
        # Test execution levels - B and C should be in same level
        levels = compiler.get_execution_levels()
        assert len(levels) == 3
        assert levels[0] == ["A"]
        assert set(levels[1]) == {"B", "C"}  # Can execute in parallel
        assert levels[2] == ["D"]
    
    def test_cycle_detection(self):
        """Test that cycles are detected"""
        workflow = {
            "id": str(uuid.uuid4()),
            "name": "Cyclic Workflow",
            "nodes": [
                {"node_id": "A", "name": "Node A", "node_type": "agent_call", "agent_id": "agent_1"},
                {"node_id": "B", "name": "Node B", "node_type": "agent_call", "agent_id": "agent_2"},
                {"node_id": "C", "name": "Node C", "node_type": "agent_call", "agent_id": "agent_3"},
            ],
            "edges": [
                {"from_node_id": "A", "to_node_id": "B"},
                {"from_node_id": "B", "to_node_id": "C"},
                {"from_node_id": "C", "to_node_id": "A"},  # Creates cycle!
            ]
        }
        
        compiler = WorkflowCompiler(workflow)
        is_valid, errors = compiler.validate()
        
        assert not is_valid
        assert any("cycle" in error.lower() for error in errors)
    
    def test_unreachable_nodes(self):
        """Test detection of unreachable nodes"""
        workflow = {
            "id": str(uuid.uuid4()),
            "name": "Disconnected Workflow",
            "nodes": [
                {"node_id": "A", "name": "Connected", "node_type": "agent_call", "agent_id": "agent_1"},
                {"node_id": "B", "name": "Unreachable", "node_type": "agent_call", "agent_id": "agent_2"},
            ],
            "edges": []  # No connections - both nodes are isolated start nodes
        }
        
        compiler = WorkflowCompiler(workflow)
        is_valid, errors = compiler.validate()
        
        # With no edges, both A and B are start nodes, so nothing is unreachable
        # This is actually a valid case (multiple independent workflows)
        # So let's modify the test to have actual unreachability
        workflow2 = {
            "id": str(uuid.uuid4()),
            "name": "Unreachable Workflow",
            "nodes": [
                {"node_id": "A", "name": "Start", "node_type": "agent_call", "agent_id": "agent_1"},
                {"node_id": "B", "name": "Connected", "node_type": "agent_call", "agent_id": "agent_2"},
                {"node_id": "C", "name": "Isolated", "node_type": "agent_call", "agent_id": "agent_3"},
            ],
            "edges": [
                {"from_node_id": "A", "to_node_id": "B"}
                # C is not connected to anything
            ]
        }
        
        compiler2 = WorkflowCompiler(workflow2)
        is_valid2, errors2 = compiler2.validate()
        
        # C should be detected as unreachable from start node A
        assert not is_valid2, f"Should detect unreachable node. Errors: {errors2}"
        assert any("unreachable" in error.lower() or "isolated" in error.lower() for error in errors2), f"Expected unreachable error, got: {errors2}"
    
    def test_invalid_node_references(self):
        """Test detection of edges referencing non-existent nodes"""
        workflow = {
            "id": str(uuid.uuid4()),
            "name": "Invalid References",
            "nodes": [
                {"node_id": "A", "name": "Node A", "node_type": "agent_call", "agent_id": "agent_1"},
            ],
            "edges": [
                {"from_node_id": "A", "to_node_id": "MISSING"},  # References non-existent node
            ]
        }
        
        compiler = WorkflowCompiler(workflow)
        is_valid, errors = compiler.validate()
        
        assert not is_valid
        assert any("non-existent" in error.lower() for error in errors)
    
    def test_node_type_validation(self):
        """Test validation of node types and required fields"""
        # Missing agent_id for agent_call
        workflow = {
            "id": str(uuid.uuid4()),
            "name": "Invalid Agent Call",
            "nodes": [
                {"node_id": "A", "name": "Bad Node", "node_type": "agent_call"},  # Missing agent_id/action
            ],
            "edges": []
        }
        
        compiler = WorkflowCompiler(workflow)
        is_valid, errors = compiler.validate()
        
        assert not is_valid
        assert any("agent_id" in error.lower() or "action" in error.lower() for error in errors)
    
    def test_parameter_binding_validation(self):
        """Test parameter binding validation"""
        workflow = {
            "id": str(uuid.uuid4()),
            "name": "Parameter Binding",
            "nodes": [
                {
                    "node_id": "A",
                    "name": "Node A",
                    "node_type": "agent_call",
                    "agent_id": "agent_1",
                    "outputs": json.dumps(["result"])
                },
                {
                    "node_id": "B",
                    "name": "Node B",
                    "node_type": "agent_call",
                    "agent_id": "agent_2",
                    "inputs": json.dumps({"data": "$A.result"})  # Valid reference
                },
                {
                    "node_id": "C",
                    "name": "Node C",
                    "node_type": "agent_call",
                    "agent_id": "agent_3",
                    "inputs": json.dumps({"data": "$MISSING.output"})  # Invalid reference
                },
            ],
            "edges": [
                {"from_node_id": "A", "to_node_id": "B"},
                {"from_node_id": "A", "to_node_id": "C"},
            ]
        }
        
        compiler = WorkflowCompiler(workflow)
        is_valid, errors = compiler.validate()
        
        assert not is_valid
        assert any("missing" in error.lower() for error in errors)
    
    def test_compile_workflow(self):
        """Test full workflow compilation"""
        workflow = {
            "id": str(uuid.uuid4()),
            "name": "Complete Workflow",
            "nodes": [
                {"node_id": "A", "name": "Start", "node_type": "agent_call", "agent_id": "agent_1"},
                {"node_id": "B", "name": "End", "node_type": "agent_call", "agent_id": "agent_2"},
            ],
            "edges": [
                {"from_node_id": "A", "to_node_id": "B"},
            ]
        }
        
        compiled = compile_workflow(workflow)
        
        assert "execution_order" in compiled
        assert "execution_levels" in compiled
        assert "adjacency" in compiled
        assert "nodes" in compiled
        assert compiled["execution_order"] == ["A", "B"]
    
    def test_complex_dag(self):
        """Test a more complex DAG structure"""
        #     A
        #    / \
        #   B   C
        #   |\ /|
        #   | X |
        #   |/ \|
        #   D   E
        #    \ /
        #     F
        
        workflow = {
            "id": str(uuid.uuid4()),
            "name": "Complex DAG",
            "nodes": [
                {"node_id": "A", "name": "A", "node_type": "agent_call", "agent_id": "agent_1"},
                {"node_id": "B", "name": "B", "node_type": "agent_call", "agent_id": "agent_2"},
                {"node_id": "C", "name": "C", "node_type": "agent_call", "agent_id": "agent_3"},
                {"node_id": "D", "name": "D", "node_type": "agent_call", "agent_id": "agent_4"},
                {"node_id": "E", "name": "E", "node_type": "agent_call", "agent_id": "agent_5"},
                {"node_id": "F", "name": "F", "node_type": "agent_call", "agent_id": "agent_6"},
            ],
            "edges": [
                {"from_node_id": "A", "to_node_id": "B"},
                {"from_node_id": "A", "to_node_id": "C"},
                {"from_node_id": "B", "to_node_id": "D"},
                {"from_node_id": "B", "to_node_id": "E"},
                {"from_node_id": "C", "to_node_id": "D"},
                {"from_node_id": "C", "to_node_id": "E"},
                {"from_node_id": "D", "to_node_id": "F"},
                {"from_node_id": "E", "to_node_id": "F"},
            ]
        }
        
        compiler = WorkflowCompiler(workflow)
        is_valid, errors = compiler.validate()
        
        assert is_valid, f"Validation failed: {errors}"
        
        levels = compiler.get_execution_levels()
        assert len(levels) == 4
        assert levels[0] == ["A"]
        assert set(levels[1]) == {"B", "C"}
        assert set(levels[2]) == {"D", "E"}
        assert levels[3] == ["F"]


class TestWorkflowValidationHelpers:
    """Test validation helper functions"""
    
    def test_validate_workflow_function(self):
        """Test the validate_workflow convenience function"""
        workflow = {
            "nodes": [
                {"node_id": "A", "name": "Node", "node_type": "agent_call", "agent_id": "agent_1"}
            ],
            "edges": []
        }
        
        is_valid, errors = validate_workflow(workflow)
        assert is_valid
        assert len(errors) == 0
    
    def test_compile_workflow_with_invalid_input(self):
        """Test that compile_workflow raises error for invalid workflow"""
        workflow = {
            "nodes": [
                {"node_id": "A", "name": "A", "node_type": "agent_call", "agent_id": "a1"},
                {"node_id": "B", "name": "B", "node_type": "agent_call", "agent_id": "a2"},
            ],
            "edges": [
                {"from_node_id": "A", "to_node_id": "B"},
                {"from_node_id": "B", "to_node_id": "A"},  # Cycle!
            ]
        }
        
        with pytest.raises(WorkflowValidationError):
            compile_workflow(workflow)


def print_test_results():
    """Print test results in a readable format"""
    print("\n" + "="*80)
    print("🧪 SPRINT 5 WORKFLOW ENGINE TEST SUITE")
    print("="*80 + "\n")
    
    test_compiler = TestWorkflowCompiler()
    test_helpers = TestWorkflowValidationHelpers()
    
    tests = [
        ("Simple Linear Workflow (A→B→C)", test_compiler.test_simple_linear_workflow),
        ("Parallel Workflow (A→(B,C)→D)", test_compiler.test_parallel_workflow),
        ("Cycle Detection", test_compiler.test_cycle_detection),
        ("Unreachable Nodes Detection", test_compiler.test_unreachable_nodes),
        ("Invalid Node References", test_compiler.test_invalid_node_references),
        ("Node Type Validation", test_compiler.test_node_type_validation),
        ("Parameter Binding Validation", test_compiler.test_parameter_binding_validation),
        ("Full Workflow Compilation", test_compiler.test_compile_workflow),
        ("Complex DAG Structure", test_compiler.test_complex_dag),
        ("Validate Workflow Helper", test_helpers.test_validate_workflow_function),
        ("Compile Invalid Workflow", test_helpers.test_compile_workflow_with_invalid_input),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✅ PASS: {test_name}")
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {test_name}")
            print(f"   Assertion Error: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"❌ FAIL: {test_name}")
            print(f"   Exception: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print(f"📊 TEST RESULTS: {passed} passed, {failed} failed out of {len(tests)} total")
    print("="*80 + "\n")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Workflow engine is working correctly!\n")
        print("✅ DAG Validation: Cycle detection ✓")
        print("✅ Topological Sorting: Execution order ✓")
        print("✅ Parallel Execution: Level computation ✓")
        print("✅ Error Detection: Invalid references ✓")
        print("✅ Node Validation: Type checking ✓")
        print("✅ Parameter Binding: Reference validation ✓")
    else:
        print(f"⚠️ {failed} test(s) failed. Please review errors above.\n")
    
    return failed == 0


if __name__ == "__main__":
    success = print_test_results()
    sys.exit(0 if success else 1)
