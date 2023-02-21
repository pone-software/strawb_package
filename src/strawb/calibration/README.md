# Calibration Data

a collection for different calibration data, like:
- [BK7](bk7.py) glass (glass of the pressure housing)
  - transmittance
  - dispersion - refraction
- [Water](water.py) models
  - a collection of 24 water publications as [csv file](water_data.csv)
  - a [csv file](water_publication.csv) listing the publications used
  - [notebook to generate the csv](../../../resources/water_absorption/water_absorption_data.ipynb), i.e. to add more data
- [LED](led.py) radiation spectra for multiple LEDs (used in STRAW-b)
- [PMT Filter](filter.py) (STRAW-b PMT-Spectrometer)
- [Camera Filter](camera_filter.csv) (STRAW-b camera)
- [Laser](laser.py) signal (STRAW-b LiDAR)
- [Bio-fouling spectra](biofouling.csv)
- [DNA damage model](dna_damage.py) and different datasets:
  - [dna absorbance](dna_absorbance.csv),
  - [Erythemal, DNA-damage, Vitamin-D](dna_absorbance_2.csv),
  - [DNA absorbance and emission](dna_absorbance_emission.csv)
  