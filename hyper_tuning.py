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

# get folder of ONE beach
def input_folder(): 
    folder_name = input('Enter the name of ONE existing folder in the repository: ').strip()
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

# helper function for intersections
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
    
# helper function to get heur 
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

def fine_tune(model, clump_model, paths, seal_conf, clump_conf, overlap_lst, clump_thresh): 
    full_metrics = pd.DataFrame(columns=['Image', 'Results', 'Seal Conf Lvl', 
                                         'Clump Conf Lvl', 'Overlap', 'Clump Threshold'])

    # iterating through possible overlap params 
    for o in overlap_lst:

        # dictionary of clumps. image id will be the key and a list of clumps will be its value. 
        clump_imgs_dct = {} 
        # number of individual seals
        ind_seals_dct = {} 

        for path in paths:

            image = Image.open(path)

            # overlap is only hyperparameter that needs to specified prior to eval 
            preds = model.predict(path, confidence=0, overlap=o).json().get('predictions', []) 

            # iterating through possible seal and clump conf params 
            for s in seal_conf: 
                for c in clump_conf: 

                    seals = [pred for pred in preds if pred['class'] == 'seals' and pred['confidence'] > s / 100]
                    clumps = [pred for pred in preds if pred['class'] == 'clump' and pred['confidence'] > c / 100]

                    # removing any intersections 
                    filtered_seals = [seal for seal in seals if not any(intersects(seal, clump) for clump in clumps)]

                    # setting key for individual seals dict 
                    key = Path(path).stem
                    ind_seals_dct[key] = len(filtered_seals) 
                    
                    # cropping images 
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

                    # iterating through clump threshold params 
                    for ct in clump_thresh: 
                        tp_clump = {key: value for key, value in clump_imgs_dct.items() if len(value) >= ct}

                        # check if there exists clumps 
                        if len(tp_clump) != 0: 

                            # heuristics 
                            df_heur = get_heuristics(tp_clump)

                            # Rand Forest on heuristics 
                            X = df_heur.drop(columns = 'key')
                            df_heur['pred_y'] = clump_model.predict(X) 
                            clump_sums = df_heur.groupby('key')['pred_y'].sum().to_dict()

                            # combining with indidivuals 
                            ind_seals_dct = dict(Counter(ind_seals_dct) + Counter(clump_sums)) 

                        # results 
                        df_results = pd.DataFrame(list(ind_seals_dct.items()), columns=['Image', 'Results'])
                        df_results['Seal Conf Lvl'] = s
                        df_results['Clump Conf Lvl'] = c
                        df_results['Overlap'] = o
                        df_results['Clump Threshold'] = ct 

                        full_metrics = pd.concat(full_metrics, df_results) 

    return full_metrics    

def main(): 

    # set up Roboflow 
    rf = Roboflow('132cxQxyrOVmPD63wJrV') # api keys are individual, change to your own
    project = rf.workspace().project('elephant-seals-project-mark-1')
    model = project.version('16').model

    # set up heuristic model 
    clump_model = load('assets/random_forest_mod1.joblib')

    # Number of beaches 
    num_beaches = input('Enter Number of Beaches to Run Tuning (each beach must have its own subdirectory of images):')

    # read in beaches, 1 per folder 
    img_dir_dct = {}
    for _ in range(int(num_beaches)): 
        path_to_beach_imgs, folder_name = input_folder() 
        img_dir_dct[folder_name] = [os.path.join(path_to_beach_imgs, file) for file in os.listdir(path_to_beach_imgs)]

    # ground truth .csv, see above for its necessary specification 
    ground_truth_file = input('Enter .csv file for ground truth')
    df_gt = pd.read_csv(ground_truth_file)

    # declaring hyperparams ranges
    seal_conf_min = input('Seal Confidence Hyperparameter Minimum')
    seal_conf_max = input('Seal Confidence Hyperparameter Maximum')
    clump_conf_min = input('Clump Confidence Hyperparameter Minimum')
    clump_conf_max = input('Clump Confidence Hyperparameter Maximum')
    overlap_min = input('Overlap Hyperparameter Minimum')
    overlap_max = input('Overlap Hyperparameter Maximum')
    clump_num_min = input('Two Prong Approach Minimum')
    clump_num_max = input('Two Prong Approach Maximum')

    # write results? 
    results_bool = input('Write Results? Enter Y or N')

    full_metrics = fine_tune(model, clump_model, img_dir_dct, range(seal_conf_min, seal_conf_max+1), 
                             range(clump_conf_min, clump_conf_max+1), range(overlap_min, overlap_max+1), 
                             range(clump_num_min, clump_num_max+1)) 

    # merging with ground truth
    full_metrics = pd.merge(full_metrics, df_gt, on='Image', how='left')

    # using % error as metric 
    full_metrics['Percent Diff'] = np.abs((full_metrics['Results']-full_metrics['Ground Truth'])/full_metrics['Ground Truth']) 

    if results_bool == 'Y':
        full_metrics.to_csv('full_metrics.csv', index=False)

    # aggregating across beaches + hyperparams 
    per_error = full_metrics.groupby(['Seal Conf Lvl', 'Clump Conf Lvl', 'Overlap', 'Clump Threshold', 'Beach'])['Percent Diff'].mean()

    # selection of best hyperparams PER beach 
    print(per_error.groupby('Beach')['Percent Diff'].min())
       

if __name__ == "__main__":
    main()










    

    
