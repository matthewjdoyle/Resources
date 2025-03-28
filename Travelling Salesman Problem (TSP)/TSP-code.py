"""
        This code will solve the travelling salesman problem for the
        nodes and edges written into the nodes-and-edges.py file using 
        the brand and bound approach
"""

from nodes_and_edges import nodes, edges

n = len(nodes)

# Initialize adjacency matrix with large values (representing infinity for no direct path)
inf = float('inf')
dist_matrix = {node: {other: inf for other in nodes} for node in nodes}

# Set distance to self as 0
for node in nodes:
    dist_matrix[node][node] = 0

# Populate the adjacency matrix with direct distances
for u, v, d in edges:
    dist_matrix[u][v] = d
    dist_matrix[v][u] = d  # Since it's an undirected graph (links have same weight in both directions)

# Apply Floyd-Warshall Algorithm to compute shortest paths between all pairs
for k in nodes:
    for i in nodes:
        for j in nodes:
            dist_matrix[i][j] = min(dist_matrix[i][j], dist_matrix[i][k] + dist_matrix[k][j])

# Print the least distance matrix into a table format
import pandas as pd
print(pd.DataFrame(dist_matrix, index=nodes, columns=nodes))



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
            # Bound: if new_cost already >= best_cost, discard
            if new_cost >= best_cost:
                continue
            branch_and_bound(node, visited | {node}, new_cost, route + [node])

branch_and_bound('Po', {'Po'}, 0, ['Po'])
print("%.2f" % best_cost, best_route)


