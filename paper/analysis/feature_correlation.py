"""Reviewer 2: pairwise correlation among the 63 predictors; clusters of near-duplicate features."""
import json, sys, numpy as np, pandas as pd
S = sys.argv[1]
F = json.load(open('analysis_R1/feature_sets.json'))['TEMPORAL_FEATURES']
df = pd.read_parquet(S, columns=F)
C = df.corr(method='pearson')
pairs = [(a, b, C.loc[a, b]) for i, a in enumerate(F) for b in F[i + 1:] if abs(C.loc[a, b]) >= 0.9]
pairs.sort(key=lambda x: -abs(x[2]))
pd.DataFrame(pairs, columns=['feature_a', 'feature_b', 'r']).to_csv('analysis_R1/results/feature_pairs_r_ge_0.9.csv', index=False)
C.to_csv('analysis_R1/results/feature_correlation_matrix.csv')
# greedy clustering: features connected by |r| >= 0.9
import itertools
parent = {f: f for f in F}
def find(x):
    while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
    return x
for a, b, r in pairs: parent[find(a)] = find(b)
groups = {}
for f in F: groups.setdefault(find(f), []).append(f)
clusters = sorted([g for g in groups.values() if len(g) > 1], key=len, reverse=True)
json.dump(clusters, open('analysis_R1/results/feature_clusters_r_ge_0.9.json', 'w'), indent=1)
print(f'{len(pairs)} pairs with |r|>=0.9 among {len(F)} features; {len(clusters)} clusters covering {sum(map(len, clusters))} features; {len(F) - sum(map(len, clusters)) + len(clusters)} effectively distinct groups')
for g in clusters: print('  ', len(g), g)
