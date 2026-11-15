"""Are the reference stations the pairing retained more urban, in LCZ terms, than those it did not?

Reviewer 1 asked about the Local Climate Zone of the selected and the non-selected sites. This tests
the share of stations in a built LCZ (classes 1-10) among the 69 stations used against the random
sample of US HadISD stations the pairing did not retain, with Fisher's exact test, so the comparison
quoted in SI Section S11 and in the reply to R1.2 can be reproduced from lcz_points.csv.

Input : <PA_OUT>/lcz_points.csv  (written by lcz_points.py)
Output: <PA_OUT>/lcz_station_comparison.json
Usage : PA_OUT=analysis_R1/results50 python3 analysis_R1/lcz_station_test.py
"""
import json, os
import pandas as pd
from scipy.stats import fisher_exact

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get('PA_OUT') or os.path.join(HERE, 'results')


def main():
    d = pd.read_csv(os.path.join(BASE, 'lcz_points.csv'), dtype={'id': str})
    d = d[d.lcz.notna()]
    out = {}
    table = []
    for kind in ['station used', 'station not used']:
        g = d[d.kind == kind]
        built = int(g.built.astype(bool).sum())
        out[kind] = {'n_classified': int(len(g)), 'n_built': built, 'pct_built': round(100 * built / len(g), 1)}
        table.append([built, len(g) - built])
    odds, p = fisher_exact(table)
    out['fisher_exact'] = {'odds_ratio': round(float(odds), 2), 'p_two_sided': round(float(p), 2)}
    json.dump(out, open(os.path.join(BASE, 'lcz_station_comparison.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
