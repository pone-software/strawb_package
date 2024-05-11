
import numpy as np
import pandas as pd

import strawb
import strawb.calibration




class InterfaceFourthDay():
    def __init__(self, fourthday, cam_device_code, z_min, z_max):
        self.fd = fourthday
        self.cam = strawb.Camera(device_code=cam_device_code)
        self.z_min = z_min
        self.z_max = z_max

        self.idx_emit, self.species, self.radii, self.mean_emission, self.sd = self.characteristics()
    

    
    def characteristics(self):
        """ 
        Get the index, species name, radius, mean emission line and standard deviation form that mean
        for each emitting organism.
        """
        idx_emit = []  # list for indices of the emitting organisms

        for i in range(len(self.fd.statistics)):
            one = self.fd.statistics[i][self.fd.statistics[i]['is_emitting']==True]
            if len(one) != 0:
                idx_emit.extend([j for j in one.index])

        idx_emit = list(np.unique(idx_emit))  # indices of organisms which emitted light at any time
                                              # of the simulation

        species = []
        radii = []

        for i in idx_emit:
            species.append(self.fd.statistics[-1].loc[i]['species'])
            radii.append(self.fd.statistics[-1].loc[i]['radius'])
 
        # mean emission line of the individual species
        mean_emission = []
        for name in species:
            for group in self.fd._life.Life.keys():
                if name in self.fd._life.Life[group][0]:
                    group_species = self.fd._life.Life[group][0].tolist()
                    index = group_species.index(name)        
                    w = self.fd._life.Life[group][1][index]
            mean_emission.append(w)

        # standard deviation of the gamma emission profile of the individual species
        sd = []
        for name in species:
            for group in self.fd._life.Life.keys():
                if name in self.fd._life.Life[group][0]:
                    group_species = self.fd._life.Life[group][0].tolist()
                    index = group_species.index(name)        
                    sd_i = self.fd._life.Life[group][2][index]
            sd.append(sd_i)

        return idx_emit, species, radii, mean_emission, sd



    def t_sim(self):
        """
        Get the timesteps at which the organisms emitted light.
        """
        t = []

        for n in self.idx_emit:
            t_i = []
            for timestep in np.arange(len(self.fd.statistics)):
                stats = self.fd.statistics[timestep]  # dataframe with information about this timestep
                if n in stats.index and stats.loc[n]['is_emitting'] == True:
                    t_i.append(timestep)
            
            t.append(t_i)

        return t



    def xy_sim(self):
        """ 
        Get x and y coordinates in the simulation for the given organisms.

        Returns
        -------
        list:
            List with [[[x_org1], [x_org2], ...], [[y_org1], [y_org2], ...]] 
            with x and y coordinates for each organism for each timestep.
        """
        x = []
        y = []

        for n in self.idx_emit: 
            x_i = []  # list for x values of organism
            y_i = []  # list for y values of organism
            for timestep in np.arange(len(self.fd.statistics)): 
                stats = self.fd.statistics[timestep]  # dataframe with information about this timestep
                # add the x, y values to the list if the organism is observed, else 'None'
                # check if n in stats.index necessary because new organisms might be injected at certain timestep
                if n in stats.index and stats.loc[n]['is_emitting'] == True:  # and stats.loc[n].observed == True:
                    x_i.append(stats.loc[n].pos_x)
                    y_i.append(stats.loc[n].pos_y)

            x.append(x_i)
            y.append(y_i)

        return [x, y]
    


    def z_sim(self):
        """Extend the 2d simulation coordinates to 3d by adding a random, constant z-value for each 
        organism (assume no current component in z-direction).
        """
##
        z_uni = np.random.uniform(self.z_min, self.z_max, len(self.idx_emit))

        t = self.t_sim()

        z = []
        for i in range(len(self.idx_emit)):
            z.append([z_uni[i]]*len(t[i]))

        return z
    


    def photon_intensity(self):
        """
        Get the number of photons emitted by the organisms per timestep.
        """
        photons = []

        for n in self.idx_emit:
            photons_i = []
            for timestep in np.arange(len(self.fd.statistics)):
                stats = self.fd.statistics[timestep]  # dataframe with information about this timestep
                if n in stats.index and stats.loc[n]['is_emitting'] == True:
                    photons_i.append(stats.loc[n]['photons'])
            
            photons.append(photons_i)

        return photons
    
        

    def org_df(self):
        """
        Get a list of dataframes with each one storing the properties of one organism.
        """
        df = []
        t = self.t_sim()
        x_sim, y_sim = self.xy_sim()
        z_sim = self.z_sim()

        photons = self.photon_intensity()

        for n in range(len(self.idx_emit)):
            df_i = pd.DataFrame()
            df_i['t'] = t[n]
            
            df_i['x_sim'] = x_sim[n]
            df_i['y_sim'] = y_sim[n]
            df_i['z_sim'] = z_sim[n]

            df_i['photons'] = photons[n]

            df.append(df_i)

        return df