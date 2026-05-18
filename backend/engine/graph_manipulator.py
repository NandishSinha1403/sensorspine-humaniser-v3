import random
import penman

class GraphManipulator:
    """
    Handles Fission (splitting) and Fusion (merging) of AMR graphs 
    to ensure sentence length variance (burstiness).
    """
    
    def apply_burstiness(self, graphs):
        """
        Takes a list of AMR graphs (strings) and applies fission/fusion.
        """
        if not graphs or len(graphs) < 2:
            return graphs
        
        manipulated_graphs = []
        skip_next = False
        
        for i in range(len(graphs)):
            if skip_next:
                skip_next = False
                continue
                
            current_graph = graphs[i]
            
            # Heuristic: 30% chance to attempt fusion with the next graph
            if i + 1 < len(graphs) and random.random() < 0.3:
                fused = self.fuse(current_graph, graphs[i+1])
                manipulated_graphs.append(fused)
                skip_next = True
            # 20% chance to attempt fission (future work: structural splitting)
            elif random.random() < 0.2:
                split_graphs = self.fission(current_graph)
                manipulated_graphs.extend(split_graphs)
            else:
                manipulated_graphs.append(current_graph)
                
        return manipulated_graphs

    def fuse(self, g1_str, g2_str):
        """
        Connects two AMR graphs using a coordinate root.
        Implements variable remapping to prevent name collisions.
        """
        try:
            # 1. Decode strings into penman Graph objects
            graph1 = penman.decode(g1_str)
            graph2 = penman.decode(g2_str)
            
            vars1 = graph1.variables()
            vars2 = graph2.variables()
            
            # 2. Create a mapping to rename variables in graph2 that collide with graph1
            mapping = {}
            used_vars = vars1.copy()
            
            for v in vars2:
                new_v = v
                counter = 1
                while new_v in used_vars:
                    new_v = f"{v}{counter}"
                    counter += 1
                mapping[v] = new_v
                used_vars.add(new_v)
            
            # 3. Remap triples in graph2
            new_triples2 = []
            for source, role, target in graph2.triples:
                new_source = mapping.get(source, source)
                new_target = mapping.get(target, target)
                new_triples2.append((new_source, role, new_target))
            
            # 4. Create coordination root concept
            coord_root = "c"
            while coord_root in used_vars:
                coord_root += "z" # Ensure unique root variable
            
            # 5. Combine all triples
            combined_triples = list(graph1.triples) + new_triples2
            combined_triples.append((coord_root, ":instance", "and"))
            combined_triples.append((coord_root, ":op1", graph1.top))
            combined_triples.append((coord_root, ":op2", mapping.get(graph2.top, graph2.top)))
            
            # 6. Encode back to AMR string
            fused_graph = penman.Graph(combined_triples, top=coord_root)
            return penman.encode(fused_graph)
            
        except Exception as e:
            print(f"CRITICAL WARNING: Structural AMR Fusion failed: {e}")
            # Fallback: Return original g1 to avoid breaking the pipeline, 
            # though this loses the second half of the information.
            return g1_str

    def fission(self, graph_str):
        """
        Structural fission: Splits a complex AMR graph into multiple logical sub-graphs.
        Trigger: If the root is an 'and' (c / and), split its :op children into independent sentences.
        This mechanically forces "Burstiness" by breaking run-on syntactic DNA.
        """
        try:
            # 1. Decode the AMR string
            graph = penman.decode(graph_str)
            root_var = graph.top
            
            # 2. Check if the root instance is 'and'
            root_instance = None
            for src, role, tgt in graph.triples:
                if src == root_var and role == ':instance':
                    root_instance = tgt
                    break
            
            if root_instance != 'and':
                return [graph_str]
            
            # 3. Identify operand variables (:op1, :op2, etc.)
            ops = []
            for src, role, tgt in graph.triples:
                if src == root_var and role.startswith(':op'):
                    ops.append(tgt)
            
            if not ops:
                return [graph_str]
            
            # 4. Extract subgraphs for each operand
            # Note: We use a simple BFS to collect all triples reachable from the op root.
            split_graphs = []
            for op_root in ops:
                visited = set()
                queue = [op_root]
                sub_triples = []
                
                # Maintain a set of all variables in the original graph for reference
                all_vars = graph.variables()
                
                while queue:
                    curr = queue.pop(0)
                    if curr in visited:
                        continue
                    visited.add(curr)
                    
                    for src, role, tgt in graph.triples:
                        # Only follow edges belonging to this branch (src is current)
                        if src == curr:
                            sub_triples.append((src, role, tgt))
                            # Follow target if it's a known variable (not a literal/number)
                            if tgt in all_vars:
                                queue.append(tgt)
                
                if sub_triples:
                    # Create the new sub-graph rooted at op_root
                    sub_graph = penman.Graph(sub_triples, top=op_root)
                    split_graphs.append(penman.encode(sub_graph))
            
            return split_graphs if split_graphs else [graph_str]
            
        except Exception as e:
            print(f"CRITICAL WARNING: Structural AMR Fission failed: {e}")
            # Safety: Return original graph to avoid data loss
            return [graph_str]
