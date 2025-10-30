"""
Workflow validation and DAG compilation service (Sprint 5)

Validates workflow structure, detects cycles, performs topological sort,
and compiles workflows into executable DAG representations.
"""
from typing import Dict, List, Set, Tuple, Any, Optional
from collections import defaultdict, deque
import json


class WorkflowValidationError(Exception):
    """Raised when workflow validation fails"""
    pass


class WorkflowCompiler:
    """
    Compiles and validates workflow DAGs.
    
    Responsibilities:
    - Validate node and edge consistency
    - Detect cycles in the DAG
    - Perform topological sort for execution order
    - Validate parameter bindings
    - Check for unreachable nodes
    """
    
    def __init__(self, workflow_dict: Dict[str, Any]):
        """
        Initialize compiler with workflow definition.
        
        Args:
            workflow_dict: Full workflow definition including nodes and edges
        """
        self.workflow = workflow_dict
        self.nodes = {node['node_id']: node for node in workflow_dict.get('nodes', [])}
        self.edges = workflow_dict.get('edges', [])
        self.adjacency: Dict[str, List[str]] = defaultdict(list)
        self.reverse_adjacency: Dict[str, List[str]] = defaultdict(list)
        self._build_adjacency_lists()
    
    def _build_adjacency_lists(self):
        """Build forward and reverse adjacency lists from edges"""
        for edge in self.edges:
            from_node = edge['from_node_id']
            to_node = edge['to_node_id']
            self.adjacency[from_node].append(to_node)
            self.reverse_adjacency[to_node].append(from_node)
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate the entire workflow.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check basic structure
        if not self.nodes:
            errors.append("Workflow must have at least one node")
            return False, errors
        
        # Validate node references in edges
        for edge in self.edges:
            from_node = edge['from_node_id']
            to_node = edge['to_node_id']
            
            if from_node not in self.nodes:
                errors.append(f"Edge references non-existent from_node: {from_node}")
            if to_node not in self.nodes:
                errors.append(f"Edge references non-existent to_node: {to_node}")
        
        # Check for cycles
        has_cycle, cycle_info = self._detect_cycle()
        if has_cycle:
            errors.append(f"Workflow contains cycle: {cycle_info}")
        
        # Check for unreachable nodes (except start nodes)
        unreachable = self._find_unreachable_nodes()
        if unreachable:
            errors.append(f"Unreachable nodes detected: {', '.join(unreachable)}")
        
        # Validate node types and required fields
        node_errors = self._validate_nodes()
        errors.extend(node_errors)
        
        # Validate parameter bindings
        binding_errors = self._validate_parameter_bindings()
        errors.extend(binding_errors)
        
        return len(errors) == 0, errors
    
    def _detect_cycle(self) -> Tuple[bool, Optional[str]]:
        """
        Detect cycles using DFS with color marking.
        
        Returns:
            Tuple of (has_cycle, cycle_description)
        """
        # 0 = white (unvisited), 1 = gray (visiting), 2 = black (visited)
        color = {node_id: 0 for node_id in self.nodes}
        parent = {}
        
        def dfs(node_id: str) -> Optional[str]:
            color[node_id] = 1  # Mark as visiting
            
            for neighbor in self.adjacency[node_id]:
                if color[neighbor] == 0:  # Unvisited
                    parent[neighbor] = node_id
                    cycle = dfs(neighbor)
                    if cycle:
                        return cycle
                elif color[neighbor] == 1:  # Back edge found - cycle!
                    # Reconstruct cycle path
                    path = [neighbor]
                    current = node_id
                    while current != neighbor and current in parent:
                        path.append(current)
                        current = parent.get(current)
                    path.append(neighbor)
                    return " -> ".join(reversed(path))
            
            color[node_id] = 2  # Mark as visited
            return None
        
        # Check all nodes (handle disconnected components)
        for node_id in self.nodes:
            if color[node_id] == 0:
                cycle = dfs(node_id)
                if cycle:
                    return True, cycle
        
        return False, None
    
    def _find_unreachable_nodes(self) -> List[str]:
        """
        Find nodes that cannot be reached from any start node.
        Start nodes are those with no incoming edges.
        """
        # Find start nodes (no incoming edges)
        start_nodes = [node_id for node_id in self.nodes 
                      if not self.reverse_adjacency[node_id]]
        
        if not start_nodes:
            # No start nodes means cycle or isolated nodes
            return []
        
        # BFS from all start nodes
        reachable = set()
        queue = deque(start_nodes)
        
        while queue:
            node_id = queue.popleft()
            if node_id in reachable:
                continue
            reachable.add(node_id)
            for neighbor in self.adjacency[node_id]:
                if neighbor not in reachable:
                    queue.append(neighbor)
        
        unreachable = [node_id for node_id in self.nodes if node_id not in reachable]
        return unreachable
    
    def _validate_nodes(self) -> List[str]:
        """Validate individual nodes for required fields and types"""
        errors = []
        valid_node_types = {'agent_call', 'tool_call', 'human_gate', 'condition', 'parallel', 'join'}
        
        for node_id, node in self.nodes.items():
            # Check node type
            node_type = node.get('node_type')
            if not node_type:
                errors.append(f"Node {node_id} missing node_type")
            elif node_type not in valid_node_types:
                errors.append(f"Node {node_id} has invalid node_type: {node_type}")
            
            # Type-specific validation
            if node_type == 'agent_call':
                if not node.get('agent_id') and not node.get('action'):
                    errors.append(f"agent_call node {node_id} must have agent_id or action")
            
            elif node_type == 'tool_call':
                if not node.get('action'):
                    errors.append(f"tool_call node {node_id} must have action")
            
            elif node_type == 'condition':
                config = node.get('config', {})
                if isinstance(config, str):
                    try:
                        config = json.loads(config)
                    except json.JSONDecodeError:
                        errors.append(f"condition node {node_id} has invalid config JSON")
                        config = {}
                
                if not config.get('condition_expression'):
                    errors.append(f"condition node {node_id} must have condition_expression in config")
        
        return errors
    
    def _validate_parameter_bindings(self) -> List[str]:
        """Validate that parameter bindings reference valid outputs"""
        errors = []
        
        # Build map of available outputs from each node
        available_outputs: Dict[str, Set[str]] = defaultdict(set)
        
        for node_id, node in self.nodes.items():
            outputs = node.get('outputs', {})
            if isinstance(outputs, str):
                try:
                    outputs = json.loads(outputs)
                except json.JSONDecodeError:
                    outputs = {}
            
            if isinstance(outputs, list):
                available_outputs[node_id].update(outputs)
            elif isinstance(outputs, dict):
                available_outputs[node_id].update(outputs.keys())
        
        # Check input bindings
        for node_id, node in self.nodes.items():
            inputs = node.get('inputs', {})
            if isinstance(inputs, str):
                try:
                    inputs = json.loads(inputs)
                except json.JSONDecodeError:
                    errors.append(f"Node {node_id} has invalid inputs JSON")
                    continue
            
            # Check if input references are valid
            for input_key, input_value in inputs.items():
                if isinstance(input_value, str) and input_value.startswith('$'):
                    # This is a reference to another node's output
                    # Format: $node_id.output_name
                    parts = input_value[1:].split('.', 1)
                    if len(parts) == 2:
                        ref_node_id, ref_output = parts
                        if ref_node_id not in self.nodes:
                            errors.append(
                                f"Node {node_id} input {input_key} references non-existent node: {ref_node_id}"
                            )
                        # Note: We don't validate output name existence here as it's runtime-dependent
        
        return errors
    
    def topological_sort(self) -> List[str]:
        """
        Perform topological sort using Kahn's algorithm.
        
        Returns:
            List of node_ids in execution order
            
        Raises:
            WorkflowValidationError if cycle is detected
        """
        # Calculate in-degrees
        in_degree = {node_id: len(self.reverse_adjacency[node_id]) for node_id in self.nodes}
        
        # Queue of nodes with no incoming edges
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        sorted_nodes = []
        
        while queue:
            node_id = queue.popleft()
            sorted_nodes.append(node_id)
            
            # Reduce in-degree for neighbors
            for neighbor in self.adjacency[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # If sorted_nodes doesn't include all nodes, there's a cycle
        if len(sorted_nodes) != len(self.nodes):
            raise WorkflowValidationError("Cannot perform topological sort: workflow contains cycle")
        
        return sorted_nodes
    
    def get_execution_levels(self) -> List[List[str]]:
        """
        Group nodes into execution levels for parallel execution.
        Nodes in the same level can be executed in parallel.
        
        Returns:
            List of levels, where each level is a list of node_ids
        """
        in_degree = {node_id: len(self.reverse_adjacency[node_id]) for node_id in self.nodes}
        levels = []
        
        while any(degree >= 0 for degree in in_degree.values()):
            # Find all nodes with in-degree 0 (current level)
            current_level = [node_id for node_id, degree in in_degree.items() if degree == 0]
            
            if not current_level:
                # No more nodes with 0 in-degree but nodes remain -> cycle
                raise WorkflowValidationError("Cannot compute execution levels: workflow contains cycle")
            
            levels.append(current_level)
            
            # Update in-degrees and mark processed nodes
            for node_id in current_level:
                in_degree[node_id] = -1  # Mark as processed
                for neighbor in self.adjacency[node_id]:
                    if in_degree[neighbor] > 0:
                        in_degree[neighbor] -= 1
        
        return levels
    
    def compile(self) -> Dict[str, Any]:
        """
        Compile workflow into executable representation.
        
        Returns:
            Compiled workflow dict with execution plan
            
        Raises:
            WorkflowValidationError if validation fails
        """
        # Validate first
        is_valid, errors = self.validate()
        if not is_valid:
            raise WorkflowValidationError(f"Workflow validation failed: {'; '.join(errors)}")
        
        # Get execution order
        execution_order = self.topological_sort()
        execution_levels = self.get_execution_levels()
        
        return {
            "workflow": self.workflow,
            "nodes": self.nodes,
            "edges": self.edges,
            "execution_order": execution_order,
            "execution_levels": execution_levels,
            "adjacency": dict(self.adjacency),
            "reverse_adjacency": dict(self.reverse_adjacency),
        }


def validate_workflow(workflow_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate a workflow.
    
    Args:
        workflow_dict: Workflow definition
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    compiler = WorkflowCompiler(workflow_dict)
    return compiler.validate()


def compile_workflow(workflow_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to compile a workflow.
    
    Args:
        workflow_dict: Workflow definition
        
    Returns:
        Compiled workflow with execution plan
        
    Raises:
        WorkflowValidationError if validation fails
    """
    compiler = WorkflowCompiler(workflow_dict)
    return compiler.compile()
