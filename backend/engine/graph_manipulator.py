import random

class GraphManipulator:
    """
    Handles Fission (splitting) and Fusion (merging) of AMR graphs 
     to ensure sentence length variance (burstiness).
    """
    
    def apply_burstiness(self, graphs):
        """
        Takes a list of AMR graphs (strings) and applies fission/fusion.
        """
        if len(graphs) < 2:
            return graphs
        
        manipulated_graphs = []
        skip_next = False
        
        for i in range(len(graphs)):
            if skip_next:
                skip_next = False
                continue
                
            current_graph = graphs[i]
            
            # Simple heuristic: 30% chance to attempt fusion with the next graph
            if i + 1 < len(graphs) and random.random() < 0.3:
                fused = self.fuse(current_graph, graphs[i+1])
                manipulated_graphs.append(fused)
                skip_next = True
            # 20% chance to attempt fission (this is harder to do purely syntactically in AMR)
            elif random.random() < 0.2:
                split_graphs = self.fission(current_graph)
                manipulated_graphs.extend(split_graphs)
            else:
                manipulated_graphs.append(current_graph)
                
        return manipulated_graphs

    def fuse(self, g1, g2):
        """
        Simple fusion: Connect two graphs using a conjunction (e.g., 'and').
        In AMR, this usually involves creating a new root node like 'and' or 'cause'.
        """
        # Placeholder: Real AMR fusion requires complex graph surgery
        # For now, we return them as is but we could wrap them in a (c / coordinate :op1 ... :op2 ...)
        return f"(c / coordinate :op1 {g1} :op2 {g2})"

    def fission(self, graph):
        """
        Simple fission: If a graph has a clear conjunction, split it.
        """
        # Placeholder: Return as is for now.
        return [graph]
