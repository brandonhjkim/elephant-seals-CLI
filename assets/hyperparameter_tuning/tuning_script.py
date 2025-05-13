"""
Inputs: 
    Directories of images of beaches, 1 for each beach 
    A .csv file for ground truths of all images. Should only have 2 columns: 'Image' and 'Ground Truth'
    Minimum and maximum for hyperparameters (will iterate over int)

Output:
    A .parquet file with all of the results 
"""

from roboflow import Roboflow
from PIL import Image
from joblib import load 
import numpy as np 
import pandas as pd
import os  
from pathlib import Path
from PIL.ExifTags import TAGS
from datetime import datetime

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
def get_heuristics(lst):
    widths = []
    heights = []
    avg_r = []
    sd_r = []
    avg_g = []
    sd_g = []
    avg_b = []
    sd_b = [] 

    for clump in lst: 
        
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

    return pd.DataFrame({'width': widths,
                        'height': heights, 'avg_r': avg_r, 
                        'sd_r': sd_r, 'avg_g': avg_g,
                        'sd_g': sd_g,'avg_b': avg_b,
                        'sd_b': sd_b})

def fine_tune(model, clump_model, beach_dct, seal_conf, clump_conf, overlap_lst): 
    full_metrics = pd.DataFrame(columns=['Beach', 'Image', 'Date', 'Seal Conf Lvl',
                                         'Clump Conf Lvl', 'Overlap', 'Number of Clumps', 
                                         'Number of Seals', 'Number of Nonintersec Seals',
                                         'Number of Seals from Clumps', 'Combined'])

    # counter stats 
    it = 0
    total = len(seal_conf)*len(clump_conf)*len(overlap_lst)*len(beach_dct) 
    chkpt_mark = 0.1 

    print(f'{int(total/len(beach_dct))} Possible Combinations')

    for beach, paths in beach_dct.items():

        for path in paths:

            # overlap params 
            for o in overlap_lst:

                # overlap is only hyperparam that needs to specified prior to eval (so only needs to access api # of possible overlap params * length of test set)
                preds = model.predict(path, confidence=0, overlap=o).json().get('predictions', []) 

                image = Image.open(path)

                # getting date
                date_str = image._getexif()[306]
                dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")

                clumps_img_dct = {} # images dict; conf as key 
                clumps_pos_dct = {} # saving raw data as well, for intersections for indiv seals; conf as key  
                for pred in preds: 
                    if pred['class'] == 'clump':
                        clump_x1 = pred['x'] - pred['width'] / 2
                        clump_x2 = pred['x'] + pred['width'] / 2
                        clump_y1 = pred['y'] - pred['height'] / 2
                        clump_y2 = pred['y'] + pred['height'] / 2

                        # saving cropped img 
                        clumps_img_dct[pred['confidence'] / 100] = image.crop((*(clump_x1, clump_y1), *(clump_x2, clump_y2)))
                        # saving raw 
                        clumps_pos_dct[pred['confidence'] / 100] = pred

                for c in clump_conf:
                    
                    # iterating across dicts, with confidence as key 
                    valid_clump_imgs = [clump_img for conf, clump_img in clumps_img_dct.items() if conf >= c / 100]
                    valid_clump_pos = [clump_pos for conf, clump_pos in clumps_pos_dct.items() if conf >= c / 100]

                    # iterating through possible seal conf params 
                    for s in seal_conf: 

                        # indiviudal seals 
                        seals = [pred for pred in preds if pred['class'] == 'seals' and pred['confidence'] > s / 100]
                        # checking intersections with clumps 
                        indivs = len([seal for seal in seals if not any(intersects(seal, clump) for clump in valid_clump_pos)])

                        # heuristic model 
                        if len(valid_clump_imgs) != 0: 
                            df_heur = get_heuristics(valid_clump_imgs)
                            clump_sums = sum(clump_model.predict(df_heur))
                        else:
                            clump_sums = 0 

                        # new entry 
                        new_entry = pd.DataFrame({
                            'Beach': [beach],
                            'Image': [Path(path).stem],
                            'Date': [dt], 
                            'Seal Conf Lvl': [s],
                            'Clump Conf Lvl': [c],
                            'Overlap': [o],
                            'Number of Clumps': [len(valid_clump_imgs)],
                            'Number of Seals': [len(seals)], 
                            'Number of Nonintersec Seals': [len(indivs)], 
                            'Number of Seals from Clumps': [clump_sums], 
                            'Combined': [indivs + clump_sums]
                        })

                        # combining 
                        full_metrics = pd.concat([full_metrics, new_entry], ignore_index=True)
                        
                        # reporting counter stats 
                        it += 1/len(paths)
                        if it/total >= chkpt_mark: 
                            print(f"{int(round(it/total, 2) * 100)}% mark reached!")
                            chkpt_mark = it/total + 0.1 

    return full_metrics    

def main(): 
    # set up Roboflow 
    rf = Roboflow('132cxQxyrOVmPD63wJrV') # api keys are individual, change to your own
    project = rf.workspace().project('elephant-seals-project-mark-1')
    model = project.version('16').model

    # set up heuristic model 
    clump_model = load('../random_forest_mod1.joblib')

    # Number of beaches 
    num_beaches = input('Enter Number of Beaches to Run Tuning (each beach must have its own subdirectory of images): ')

    # read in beaches, 1 per folder 
    img_dir_dct = {}
    for _ in range(int(num_beaches)): 
        path_to_beach_imgs, folder_name = input_folder() 
        img_dir_dct[folder_name] = [os.path.join(path_to_beach_imgs, file) for file in os.listdir(path_to_beach_imgs)]

    # ground truth .csv, see above for its necessary specification 
    ground_truth = input('Enter .csv file for ground truth: ')
    ground_truth_path = os.path.join(os.getcwd(), ground_truth)
    if not os.path.isfile(ground_truth_path):
        raise FileNotFoundError(f"The file '{ground_truth_path}' does not exist in the current directory.")
    df_gt = pd.read_csv(ground_truth)

    # declaring hyperparams ranges
    print('For the following hyperparameters, space the minimum, maximum and step with spaces (e.g. 20 40 2)')
    seal_conf_min, seal_conf_max, seal_range = map(int, input('Seal Confidence Hyperparameter Range: ').split())
    clump_conf_min, clump_conf_max, clump_range = map(int, input('Clump Confidence Hyperparameter Range: ').split())
    overlap_min, overlap_max, overlap_range = map(int, input('Overlap Hyperparameter Range: ').split())

    # save results to?
    results_path_name = input("Save Results to? (Don't include .parquet in name) ")

    # run fine tuning func 
    full_metrics = fine_tune(model, clump_model, img_dir_dct, 
                             range(seal_conf_min, seal_conf_max+1, seal_range), 
                             range(clump_conf_min, clump_conf_max+1, clump_range), 
                             range(overlap_min, overlap_max+1, overlap_range)
                             ) 

    # merging with ground truth
    full_metrics = pd.merge(full_metrics, df_gt, on='Image', how='left')
    full_metrics.to_parquet(f'{results_path_name}.parquet', index=False)
    print(f'Results have been saved to {results_path_name}.parquet')
       
if __name__ == "__main__":
    main()










    

    
