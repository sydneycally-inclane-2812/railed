import matplotlib.pyplot as plt
import networkx as nx

class DrawMap:
    def __init__(self, show_labels=True, figsize=(8, 6)):
        self.show_labels = show_labels
        self.figsize = figsize

    def draw(self, map_obj):
        """
        Draws the train network map using matplotlib and networkx.
        Nodes are stations, edges are lines.
        Each line is colored uniquely.
        """
        G = map_obj.graph
        pos = nx.spring_layout(G, seed=42)  # You can use a custom layout if you have coordinates
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
