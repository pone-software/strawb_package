import pandas

from strawb.calibration.absorption import Absorption


class Water(Absorption):
    config_parameters_pool = pandas.read_parquet('water_data.parquet')

    def __init__(self, thickness=None, publication='hale73', config_parameters=None):
        """Class to calculate the water absorption based on data (wavelength vs. absorption).
        Several publications are combined into a single dataset (pandas.DataFrame).
        See 'config_parameters_pool' for available publication strings.
        PARAMETER
        ---------
        publication: str, optional
            defines which dataset is selected from the `config_parameters_pool`.
            If a dataset is provided, with the `config_parameters` parameter, `publication` is ignored.
            See all valid publication strings with: `config_parameters_pool.publication.unique()`
        thickness: float, optional
            the thickness of the glass in meter [m].
        config_parameters: pandas.DataFrame, optional
            to define the absorption length of the glass.
            The DataFrame must have the columns 'wavelength'(in nm) and 'absorption'(in [1/m]).
            The 'absorption' is the absorption coefficient or 1./'absorption_length'.
        """
        if config_parameters is None:
            if 0 < (self.config_parameters_pool.publication == 'hale73').sum():
                df_i = self.config_parameters_pool
                config_parameters = df_i[df_i.publication == 'hale73'].copy()
            else:
                raise KeyError(f'publication not in config_parameters_pool. Got: {publication}')

        Absorption.__init__(self, thickness=thickness, config_parameters=config_parameters)
