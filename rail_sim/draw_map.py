import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

class DrawMap:
    def __init__(self, show_labels=True, figsize=(8, 6)):
        self.show_labels = show_labels
        self.figsize = figsize

    def draw(self, map_obj):
        """
        Draws the train network map using matplotlib and networkx.
        Nodes are stations, edges are lines.
        Each line is colored uniquely.
        Multiple lines on the same edge are drawn as parallel lines with offsets.
        """
        G = map_obj.graph
        
        # Use kamada_kawai layout for balanced edge lengths
        # Then apply additional spacing with spring layout refinement
        try:
            # First pass: kamada-kawai for good initial positions
            pos = nx.kamada_kawai_layout(G)
            # Second pass: spring layout to push nodes apart (acts as repulsion)
            pos = nx.spring_layout(G, pos=pos, iterations=50, k=0.75, seed=42)
        except:
            # Fallback to pure spring layout
            pos = nx.spring_layout(G, k=0.5, iterations=200, seed=42)
        
        fig, ax = plt.subplots(figsize=self.figsize)

        # Collect edges grouped by line
        lines_edges = {}
        for u, v, key, data in G.edges(keys=True, data=True):
            line_code = data.get('line', 'Unknown')
            if line_code not in lines_edges:
                lines_edges[line_code] = []
            lines_edges[line_code].append((u, v))
        
        # Create color map
        line_codes = sorted(lines_edges.keys())
        color_map = {code: plt.cm.tab10(i % 10) for i, code in enumerate(line_codes)}

        # Group edges by station pair to detect shared edges
        edge_counts = {}
        for u, v, key, data in G.edges(keys=True, data=True):
            edge_pair = tuple(sorted([u, v]))
            edge_counts[edge_pair] = edge_counts.get(edge_pair, 0) + 1

        # Draw each line's edges with offset if multiple lines share the edge
        for line_code, edges in lines_edges.items():
            for u, v in edges:
                edge_pair = tuple(sorted([u, v]))
                num_lines = edge_counts[edge_pair]
                
                if num_lines == 1:
                    # Single line - draw normally
                    ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], 
                           color=color_map[line_code], linewidth=3, 
                           label=line_code if line_code not in ax.get_legend_handles_labels()[1] else "",
                           zorder=1)
                else:
                    # Multiple lines - draw with offset
                    # Get all lines on this edge
                    lines_on_edge = []
                    for uu, vv, key, data in G.edges(keys=True, data=True):
                        if tuple(sorted([uu, vv])) == edge_pair:
                            lines_on_edge.append(data.get('line'))
                    
                    # Calculate offset for this line
                    line_idx = sorted(lines_on_edge).index(line_code)
                    offset_distance = 0.005  # Adjust this to control spacing
                    offset = (line_idx - (num_lines - 1) / 2) * offset_distance
                    
                    # Calculate perpendicular offset vector
                    dx = pos[v][0] - pos[u][0]
                    dy = pos[v][1] - pos[u][1]
                    length = np.sqrt(dx**2 + dy**2)
                    if length > 0:
                        perp_x = -dy / length * offset
                        perp_y = dx / length * offset
                    else:
                        perp_x, perp_y = 0, 0
                    
                    # Draw offset line
                    ax.plot([pos[u][0] + perp_x, pos[v][0] + perp_x], 
                           [pos[u][1] + perp_y, pos[v][1] + perp_y],
                           color=color_map[line_code], linewidth=2.5, 
                           label=line_code if line_code not in ax.get_legend_handles_labels()[1] else "",
                           zorder=1)

        # Draw nodes
        for node in G.nodes():
            ax.plot(pos[node][0], pos[node][1], 'o', 
                   markersize=20, color="#ffe066", 
                   markeredgecolor="#333", markeredgewidth=1.5, zorder=2)
        
        # Draw labels
        if self.show_labels:
            for node in G.nodes():
                label = map_obj.stations[node].name if node in map_obj.stations else str(node)
                ax.text(pos[node][0], pos[node][1], label, 
                       fontsize=9, ha='center', va='center', zorder=3)

        ax.set_title("Train Network Map")
        ax.axis('off')
        ax.legend(loc='best', fontsize=10)
        plt.tight_layout()
        plt.show()

# Example usage:
# from rail_sim.map import Map
# from rail_sim.draw_map import DrawMap
# map_obj = Map()
# ... add lines and stations ...
# DrawMap().draw(map_obj)
