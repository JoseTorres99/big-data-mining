import csv
import networkx as nx
import matplotlib.pyplot as plt

# Create directed graph
G = nx.DiGraph()

# Read graph.csv
with open("graph.csv", "r", newline="", encoding="utf-8") as file:
    reader = csv.reader(file)
    for row in reader:
        # Remove extra spaces and ignore empty values
        row = [item.strip() for item in row if item.strip()]
        if len(row) < 1:
            continue

        parent = row[0]

        # Make sure parent exists even if it has no children
        G.add_node(parent)

        # Add directed edges from parent to each child
        for child in row[1:]:
            G.add_edge(parent, child)

# Run PageRank
pagerank_scores = nx.pagerank(G)

# Print PageRank weights
print("PageRank Weights:")
for node, score in pagerank_scores.items():
    print(f"{node}: {score:.6f}")

# Node sizes = weight * 3000
node_sizes = [pagerank_scores[node] * 3000 for node in G.nodes()]

# Draw graph
plt.figure(figsize=(10, 8))
pos = nx.spring_layout(G, seed=42)

nx.draw(
    G,
    pos,
    with_labels=True,
    node_size=node_sizes,
    node_color="lightblue",
    arrows=True,
    font_size=10
)

plt.title("Directed Graph with PageRank Node Sizes")
plt.show()