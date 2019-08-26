from photonai.base.PhotonBase import Hyperpipe, PipelineElement, OutputSettings, PreprocessingPipe
from photonai.optimization.Hyperparameters import FloatRange, Categorical, IntegerRange
from photonai.neuro.AtlasMapping import AtlasMapper
from photonai.neuro.NeuroBase import NeuroModuleBranch
from sklearn.model_selection import KFold
import time
import os
import pandas as pd
import glob
import numpy as np
import warnings

from photonai.base.PhotonBase import PipelineElement, PreprocessingPipe, Hyperpipe
from photonai.neuro.BrainAtlas import BrainAtlas


#load nifti files
file_path_list = glob.glob('/spm-data/Scratch/spielwiese_vincent/PAC2019/CAT12_JC/mri/mwp1age*.nii')
#print(file_path_list)
X = sorted(file_path_list)
#print(X)



#load labels
PAClabels = pd.DataFrame(pd.read_excel(r'/spm-data/Scratch/spielwiese_ramona/PAC2019/old_files/PAC2019_data.xlsx'))
PAClabels = PAClabels[['id', 'age']]
PACIDs = [z.split("/mri/mwp1")[1].split("_")[0] for z in file_path_list]
SelectedLabels = PAClabels[PAClabels['id'].isin(PACIDs)]
y = SelectedLabels['age'].to_numpy()
print(np.isnan(y))
print(type(y))



warnings.filterwarnings("ignore", category=DeprecationWarning)

# YOU CAN SAVE THE TRAINING AND TEST RESULTS AND ALL THE PERFORMANCES IN THE MONGODB
mongo_settings = OutputSettings(save_predictions='best')


# DESIGN YOUR PIPELINE
my_pipe = Hyperpipe('Brain_Atlas_Pipe',  # the name of your pipeline
                    optimizer='grid_search',  # which optimizer PHOTON shall use
                    metrics=['mean_absolute_error', 'mean_squared_error'],  # the performance metrics of your interest
                    best_config_metric='mean_absolute_error',
                    inner_cv=KFold(n_splits=3),  # test each configuration ten times respectively,
                    verbosity=3,
                    output_settings=mongo_settings)  # get error, warn and info message


brain_atlas = PipelineElement('BrainAtlas', atlas_name="AAL", extract_mode='vec',
                                rois='all')

neuro_branch = NeuroModuleBranch('NeuroBranch')
neuro_branch += brain_atlas

my_pipe += PipelineElement('SVR', hyperparameters={}, kernel='linear')

# NOW TRAIN YOUR PIPELINE
my_folder = '/spm-data/Scratch/spielwiese_vincent/PAC2019/CAT12_JC/AtlasMapper_AAL'
atlas_mapper = AtlasMapper()
atlas_mapper.generate_mappings(my_pipe, neuro_branch, my_folder)
atlas_mapper.fit(X, y)

# LOAD TRAINED ATLAS MAPPER AND PREDICT
atlas_mapper = AtlasMapper()
atlas_mapper.load_from_file('/spm-data/Scratch/spielwiese_nils_winter/atlas_mapper_test_oasis/Brain_Atlas_Pipe_atlas_mapper_meta.json')

#print(atlas_mapper.predict(X))
