import matplotlib.pyplot as plt
import networkx as nx

class DrawMap:
    def __init__(self, show_labels=True, figsize=(8, 6), layout='kamada_kawai'):
        """
        Initialize map drawer.
        
        layout options:
        - 'kamada_kawai': Force-directed, good for minimizing edge crossings (default)
        - 'planar': Attempts planar layout (no crossings) if graph is planar
        - 'spring': Force-directed with springs (can be messy)
        - 'circular': Nodes in a circle
        - 'shell': Concentric circles
        - 'spectral': Uses graph Laplacian eigenvectors
        """
        self.show_labels = show_labels
        self.figsize = figsize
        self.layout = layout

    def draw(self, map_obj):
        """
        Draws the train network map using matplotlib and networkx.
        Nodes are stations, edges are lines.
        Each line is colored uniquely.
        """
        G = map_obj.graph
        
        # Choose layout algorithm
        if self.layout == 'kamada_kawai':
            pos = nx.kamada_kawai_layout(G)
        elif self.layout == 'planar':
            if nx.is_planar(G):
                pos = nx.planar_layout(G)
            else:
                print("Graph is not planar, falling back to kamada_kawai")
                pos = nx.kamada_kawai_layout(G)
        elif self.layout == 'spring':
            pos = nx.spring_layout(G, seed=42, k=0.5, iterations=50)
        elif self.layout == 'circular':
            pos = nx.circular_layout(G)
        elif self.layout == 'shell':
            pos = nx.shell_layout(G)
        elif self.layout == 'spectral':
            pos = nx.spectral_layout(G)
        else:
            pos = nx.kamada_kawai_layout(G)  # Default
        plt.figure(figsize=self.figsize)

        # Get all line codes for coloring
        edge_lines = nx.get_edge_attributes(G, 'line')
        line_codes = list(set(edge_lines.values()))
        color_map = {code: plt.cm.tab10(i % 10) for i, code in enumerate(line_codes)}

        # Draw edges by line
        for line_code in line_codes:
            edges = [(u, v) for (u, v), l in edge_lines.items() if l == line_code]
            nx.draw_networkx_edges(G, pos, edgelist=edges, width=3, edge_color=[color_map[line_code]], label=f"Line {line_code}")

        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_size=400, node_color="#ffe066", edgecolors="#333")
        if self.show_labels:
            labels = {sid: map_obj.stations[sid].name if sid in map_obj.stations else str(sid) for sid in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels, font_size=10)

        plt.title("Train Network Map")
        plt.axis('off')
        plt.legend()
        plt.tight_layout()
        plt.show()

# Example usage:
# from rail_sim.map import Map
# from rail_sim.draw_map import DrawMap
# map_obj = Map()
# ... add lines and stations ...
# DrawMap().draw(map_obj)
