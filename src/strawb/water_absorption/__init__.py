import os

import pandas
from .data import morel77_df, morel07_df, quickenden80_df, straw21_df, km3net15_df
import strawb

all_publication_df = pandas.read_pickle(os.path.join(strawb.__path__[0],
                                                     'water_absorption/data.gz'))

for i in [morel77_df, morel07_df, quickenden80_df, straw21_df, km3net15_df]:
    all_publication_df = all_publication_df.append(i, ignore_index=True)