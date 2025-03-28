# Define a list of nodes
nodes = ["Po", "Ho", "Ha", "Hp", "Bp", "Le", "St", "Cg", "Bm"]
n = len(nodes)

# Initialize adjacency matrix with large values (representing infinity for no direct path)
inf = float('inf')
dist_matrix = {node: {other: inf for other in nodes} for node in nodes}

# Set distance to self as 0
for node in nodes:
    dist_matrix[node][node] = 0

# Define links between nodes with distances
edges = [
    ("Po", "Ho", 1.6), ("Po", "Ha", 3.7), ("Po", "Hp", 4.18), ("Po", "Bm", 5.6),
    ("Ho", "Ha", 2.25), ("Ho", "Hp", 3.1), ("Ha", "Hp", 1.1), 
    ("Hp", "Bp", 0.95), ("Hp", "Cg", 2.25), ("Ho", "Le", 5.3),
    ("Bp", "Le", 1.93), ("Bp", "Cg", 1.91),
    ("Cg", "Bm", 0.97), ("Cg", "St", 1.93), ("Cg", "Le", 1.5),
    ("Bm", "St", 2.25), ("Le", "St", 2.25)
]

# Populate the adjacency matrix with direct distances
for u, v, d in edges:
    dist_matrix[u][v] = d
    dist_matrix[v][u] = d  # Since it's an undirected graph (links have same weight in both directions)

# Apply Floyd-Warshall Algorithm to compute shortest paths between all pairs
for k in nodes:
    for i in nodes:
        for j in nodes:
            dist_matrix[i][j] = min(dist_matrix[i][j], dist_matrix[i][k] + dist_matrix[k][j])

# Convert the result into a table format
import pandas as pd
df = pd.DataFrame(dist_matrix, index=nodes, columns=nodes)
print(df)



import math
# Use the nodes list and dist_matrix defined earlier.
best_cost = math.inf
best_route = None

def branch_and_bound(current, visited, cost, route):
    global best_cost, best_route
    # If visited all nodes, return to starting node (which is 'Ho')
    if len(visited) == len(nodes):
        total_cost = cost + dist_matrix[current]['Po']
        if total_cost < best_cost:
            best_cost = total_cost
            best_route = route + ['Po']
        return

    # Branch: try each node that hasn't been visited
    for node in nodes:
        if node not in visited:
            new_cost = cost + dist_matrix[current][node]
            # Bound: if new_cost already >= best_cost, prune
            if new_cost >= best_cost:
                continue
            branch_and_bound(node, visited | {node}, new_cost, route + [node])

branch_and_bound('Po', {'Po'}, 0, ['Po'])
print(best_cost, best_route)
