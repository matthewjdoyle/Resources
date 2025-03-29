# Define a list of nodes
nodes = ["Gh", "Ho", "Ot", "Hp", "Bp", "Jh", "Po", "Ca", "Bb"]
# Define a list of tuples to act as edges
edges = [
    ("Gh", "Ho", 1.6), ("Gh", "Ot", 3.9), ("Gh", "Hp", 4.2), ("Gh", "Bb", 5.8),
    ("Ho", "Ot", 2.3), ("Ho", "Hp", 3), ("Ot", "Hp", 1.1), 
    ("Hp", "Bp", 0.9), ("Hp", "Ca", 2.2), ("Ho", "Jh", 5.1),
    ("Bp", "Jh", 1.9), ("Bp", "Ca", 1.9),
    ("Ca", "Bb", 0.9), ("Ca", "Po", 1.9), ("Ca", "Jh", 1.5),
    ("Bb", "Po", 2.2), ("Jh", "Po", 2.2)
]
