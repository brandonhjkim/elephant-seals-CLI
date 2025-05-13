from roboflow import Roboflow
from PIL import Image
from joblib import load 
import numpy as np 
import pandas as pd
import os 
from collections import Counter 
from pathlib import Path

def input_folder():
    """
    Prompts the user to choose a folder from the current working directory.
    """
    print()
    # Display the base directory and its subdirectories for the user to choose from.
    # print(f"Mounted base directory: {base_dir}")
    print()
    print("Available subdirectories:")
    entries = os.listdir('.')
    base_dir = os.getcwd()
    subdirs = [entry for entry in entries if os.path.isdir(os.path.join(base_dir, entry))]
    if not subdirs:
        print("|- No subdirectories found in the base directory.")
    else:
        for sub in subdirs:
            print(f"|- {sub}")
    
    print()
    folder_name = input('Enter the name of an existing folder from the mounted directory (or type "exit" to quit): ').strip()
    if folder_name.lower() == "exit":
        return None  # Signal to exit

    # Use the BASE_DIR as the base for relative paths.
    folder_path = os.path.join(base_dir, folder_name)
    if not os.path.isdir(folder_path):
        raise ValueError(f"The folder '{folder_path}' does not exist.")
    
    def is_image_file(filename):
        image_extensions = {'.png', '.jpg', '.jpeg', '.tif', '.tiff'}
        return any(filename.lower().endswith(ext) for ext in image_extensions)
    
    files = os.listdir(folder_path)
    if not all(is_image_file(file) for file in files if os.path.isfile(os.path.join(folder_path, file))):
        raise ValueError(f"The folder '{folder_name}' contains non-image files.")
    
    print(f"Folder '{folder_path}' is valid. Running the detection model...")
    return folder_path

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

        for idx, clump in enumerate(clump_lst): 
        
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

def main(): 

    # Obtain Roboflow API key: environment variable or prompt with default
    default_api_key = "132cxQxyrOVmPD63wJrV"
    api_key = os.environ.get("ROBOFLOW_API_KEY")
    if not api_key:
        user_input = input("Enter Roboflow API key (or press Enter to use default): ").strip()
        api_key = user_input or default_api_key
        if not api_key:
            raise ValueError("No Roboflow API key provided.")
        print("Using Roboflow API key:", "default" if not user_input else "user-provided")
    rf = Roboflow(api_key=api_key)
    project = rf.workspace().project('elephant-seals-project-mark-1')
    model = project.version('16').model

    while True:
        path_to_beach_imgs = input_folder()
        if path_to_beach_imgs is None:
            print("Exiting the program.")
            break

        beach_imgs_paths = [os.path.join(path_to_beach_imgs, file) for file in os.listdir(path_to_beach_imgs)]

        # our preset values of min confidence and overlap, based on vibes
        clumps, indivs = get_indivs_and_clumps(model, beach_imgs_paths, seal_conf_lvl = 20, clump_conf_lvl = 40, overlap = 20) 

        clumps = {key: value for key, value in clumps.items() if len(value) >= 10}

        if len(clumps) != 0:

            df_heur = get_heuristics(clumps)

            clump_model = load('./random_forest_mod1.joblib')

            X = df_heur.drop(columns = 'key')
            df_heur['pred_y'] = clump_model.predict(X) 

            clump_sums = df_heur.groupby('key')['pred_y'].sum().to_dict()

            indivs = dict(Counter(indivs) + Counter(clump_sums)) 

        for key, value in indivs.items():
            print(f'{key} Number of Seals: {value}')
        print("In total, we have", sum(indivs.values()), "seals")

if __name__ == "__main__":
    main()
