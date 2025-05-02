"""
Inputs: 
    Directories of images of beaches
    A .csv file for ground truths of all images. Should only have 2 columns: 'Image' and 'Results'
    Minimum and maximum for hyperparameters (will iterate over int)

Printed Output:
    Results from hyperparameter tuning, with best combination of hyperparameters subsetted by each beach. 
    It currently utilizes average percent error as metric 
"""

from roboflow import Roboflow
from PIL import Image
from joblib import load 
import numpy as np 
import pandas as pd
import os 
from collections import Counter 
from pathlib import Path

def input_folder(): 
    folder_name = input('Enter the name of one existing folder in the repository: ').strip()
    folder_path = os.path.join(os.getcwd(), folder_name)

    if not os.path.isdir(folder_path):
        raise ValueError(f"The folder '{folder_name}' does not exist in the repository.")

    def is_image_file(filename):
        image_extensions = {'.png', '.jpg', '.jpeg', '.tif', '.tiff'}
        return any(filename.lower().endswith(ext) for ext in image_extensions)

    files = os.listdir(folder_path)
    if not all(is_image_file(file) for file in files if os.path.isfile(os.path.join(folder_path, file))):
        raise ValueError(f"The folder '{folder_name}' contains non-image files.")

    print(f"Folder '{folder_name}' is valid and contains only image files.")
    
    return folder_path, folder_name

def get_indivs_and_clumps(model, paths, seal_conf_lvl, clump_conf_lvl, overlap): 
    clump_imgs_dct = {} # dictionary of clumps. image id will be the key and a list of clumps will be its value. 
    ind_seals_dct = {} # number of individual seals 

    def intersects(seal, clump):
        seal_x1 = seal['x'] - seal['width'] / 2
        seal_x2 = seal['x'] + seal['width'] / 2
        seal_y1 = seal['y'] - seal['height'] / 2
        seal_y2 = seal['y'] + seal['height'] / 2

        clump_x1 = clump['x'] - clump['width'] / 2
        clump_x2 = clump['x'] + clump['width'] / 2
        clump_y1 = clump['y'] - clump['height'] / 2
        clump_y2 = clump['y'] + clump['height'] / 2

        return not (
            seal_x2 <= clump_x1 or
            seal_x1 >= clump_x2 or
            seal_y2 <= clump_y1 or
            seal_y1 >= clump_y2
        )

    for path in paths:

        image = Image.open(path)

        preds = model.predict(path, confidence=min(seal_conf_lvl, clump_conf_lvl), overlap=overlap).json().get('predictions', []) 

        seals = [pred for pred in preds if pred['class'] == 'seals' and pred['confidence'] > seal_conf_lvl / 100]
        clumps = [pred for pred in preds if pred['class'] == 'clump' and pred['confidence'] > clump_conf_lvl / 100]
        filtered_seals = [seal for seal in seals if not any(intersects(seal, clump) for clump in clumps)]

        # getting key
        key = Path(path).stem

        # adding to individuals dict
        ind_seals_dct[key] = len(filtered_seals) 
        
        # adding to clumps dict
        clump_imgs_dct[key] = [] 
        for clump in clumps:
            clump_x1 = clump['x'] - clump['width'] / 2
            clump_x2 = clump['x'] + clump['width'] / 2
            clump_y1 = clump['y'] - clump['height'] / 2
            clump_y2 = clump['y'] + clump['height'] / 2

            top_left_clump = (clump_x1, clump_y1)
            bottom_right_clump = (clump_x2, clump_y2)

            subimage = image.crop((*top_left_clump, *bottom_right_clump))
            
            clump_imgs_dct[key].append(subimage)
    
    return clump_imgs_dct, ind_seals_dct

def get_heuristics(dct):
    widths = []
    heights = []
    avg_r = []
    sd_r = []
    avg_g = []
    sd_g = []
    avg_b = []
    sd_b = [] 

    keys = []

    for key, clump_lst in dct.items():

        for _, clump in enumerate(clump_lst): 
        
            width, height = clump.size

            widths.append(width)
            heights.append(height)

            img_array = np.array(clump)

            avg_r.append(np.mean(img_array[1, :, :]))
            sd_r.append(np.std(img_array[1, :, :]))
            avg_g.append(np.mean(img_array[:, 1, :]))
            sd_g.append(np.std(img_array[:, 1, :]))
            avg_b.append(np.mean(img_array[:, :, 1]))
            sd_b.append(np.std(img_array[:, :, 1]))

            keys.append(key)

    return pd.DataFrame({'key': keys, 'width': widths,
                        'height': heights, 'avg_r': avg_r, 
                        'sd_r': sd_r, 'avg_g': avg_g,
                        'sd_g': sd_g,'avg_b': avg_b,
                        'sd_b': sd_b})

def single_run(model, filenames, seal_conf_lvl, clump_conf_lvl, overlap, clump_num): 

    clumps, indivs = get_indivs_and_clumps(model, filenames, seal_conf_lvl = 20, clump_conf_lvl = 40, overlap = 20) 

    clumps = {key: value for key, value in clumps.items() if len(value) >= clump_num}

    if len(clumps) != 0: 

        clump_model = load('assets/random_forest_mod1.joblib')

        df_heur = get_heuristics(clumps)

        X = df_heur.drop(columns = 'key')
        df_heur['pred_y'] = clump_model.predict(X) 

        clump_sums = df_heur.groupby('key')['pred_y'].sum().to_dict()

        indivs = dict(Counter(indivs) + Counter(clump_sums)) 

    return indivs        

def main(): 

    rf = Roboflow('132cxQxyrOVmPD63wJrV') # api keys are individual, change to your own
    project = rf.workspace().project('elephant-seals-project-mark-1')
    model = project.version('16').model

    img_dir_dct = {}

    num_beaches = input('Enter Number of Beaches to Run Tuning (each beach must have its own subdirectory of images):')

    for _ in range(int(num_beaches)): 
        path_to_beach_imgs, folder_name = input_folder() 
        img_dir_dct[folder_name] = [os.path.join(path_to_beach_imgs, file) for file in os.listdir(path_to_beach_imgs)]

    ground_truth_file = input('Enter .csv file for ground truth')
    df_gt = pd.read_csv(ground_truth_file)

    seal_conf_min = input('Seal Confidence Hyperparameter Minimum')
    seal_conf_max = input('Seal Confidence Hyperparameter Maximum')
    clump_conf_min = input('Clump Confidence Hyperparameter Minimum')
    clump_conf_max = input('Clump Confidence Hyperparameter Maximum')
    overlap_min = input('Overlap Hyperparameter Minimum')
    overlap_max = input('Overlap Hyperparameter Maximum')
    clump_num_min = input('Two Prong Approach Minimum')
    clump_num_max = input('Two Prong Approach Maximum')

    results_bool = input('Write Results? Enter Y or N')

    full_metrics = pd.DataFrame(columns=['Image', 'Results', 'Seal Conf Lvl', 
                                         'Clump Conf Lvl', 'Overlap', 'Clump Threshold'])

    for seal_conf_lvl in range(seal_conf_min, seal_conf_max+1):
        for clump_conf_lvl in range(clump_conf_min, clump_conf_max+1):
            for overlap in range(overlap_min, overlap_max+1):
                for clump_num in range(clump_num_min, clump_num_max+1):
                    for beach, imgs in img_dir_dct.items():

                        results = single_run(model, imgs, seal_conf_lvl, clump_conf_lvl, overlap, clump_num)

                        df_results = pd.DataFrame(list(results.items()), columns=['Image', 'Results'])
                        df_results['Seal Conf Lvl'] = seal_conf_lvl
                        df_results['Clump Conf Lvl'] = clump_conf_lvl
                        df_results['Overlap'] = overlap
                        df_results['Clump Threshold'] = clump_num 

                        full_metrics = pd.concat(full_metrics, results) 

    full_metrics = pd.merge(full_metrics, df_gt, on='Image', how='left')

    full_metrics['Percent Diff'] = np.abs((full_metrics['Results']-full_metrics['Ground Truth'])/full_metrics['Ground Truth']) 

    if results_bool == 'Y':
        full_metrics.to_csv('full_metrics.csv', index=False)

    per_error = full_metrics.groupby(['Seal Conf Lvl', 'Clump Conf Lvl', 'Overlap', 'Clump Threshold', 'Beach'])['Percent Diff'].mean()

    print(per_error.groupby('Beach')['Percent Diff'].min())
       

if __name__ == "__main__":
    main()










    

    
