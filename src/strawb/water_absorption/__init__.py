import os

import pandas
import data
import strawb

all_publication_df = pandas.read_pickle(os.path.join(strawb.__path__[0],
                                                     'water_absorption/data.gz'))

for i in [data.morel77_df,
          data.morel07_df,
          data.quickenden80_df]:
    all_publication_df = all_publication_df.append(i, ignore_index=True)