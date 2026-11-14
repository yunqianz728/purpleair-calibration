"""Convert the published paired dataset to the Parquet file the analysis scripts read.

Every script here reads the same 797,744-row table. As gzipped CSV it takes about a minute to
parse and is re-parsed by each script; as Parquet it loads in a second and lets a script ask for
three columns instead of ninety-nine. The two hold identical data -- this writes one from the other
and checks that the column set survives the round trip.

Input : data/training_data_with_classification.csv.gz
Output: analysis_R1/train.parquet  (or $PA_PARQUET)
Usage : python3 analysis_R1/make_parquet.py
"""
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.environ.get('PA_CSV', os.path.join(HERE, '..', 'data', 'training_data_with_classification.csv.gz'))
OUT = os.environ.get('PA_PARQUET', os.path.join(HERE, 'train.parquet'))


def main():
    print(f'reading {CSV} ...', flush=True)
    df = pd.read_csv(CSV, low_memory=False)
    df.to_parquet(OUT)
    back = pd.read_parquet(OUT, columns=None).columns
    assert set(back) == set(df.columns), 'column set changed in the round trip'
    print(f'wrote {OUT}: {len(df):,} rows x {len(df.columns)} columns')
    print('point the analysis scripts at it with:  export PA_PARQUET=' + os.path.abspath(OUT))


if __name__ == '__main__':
    main()
