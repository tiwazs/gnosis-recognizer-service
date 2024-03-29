import argparse
import base64
import json
import os
from typing import List
from typing_extensions import TypedDict
import imutils
import insightface
import cv2
import sys
import numpy as np
from mxnet.base import _NullType
from pathlib import Path
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))
from videoAnalytics.utils import scaller_conc


#This script  gets the embedding of a set of images.
#Receives a json containing the path to siad images as input.
#{"felipe":["imgs/felipe/felipe1.jpg","imgs/felipe/felipe7.jpg"], "vincent":["imgs/vincent/00000002.jpg","imgs/vincent/00000024.jpg"]}
#Returns a json containing the embedding of each image to be stored or processed.
#This script can be called from terminal. 
#: Create a another python script to test this script independenly
class InputData(TypedDict):
    key: List[str]

class OutputEncodding(TypedDict):
    img: str
    embedding: List[float]

class OutputData(TypedDict):
    key: List[OutputEncodding]        

class encoderExtractor:
    def __init__(self, input_data: InputData, detector, recognizer) -> None:
        if input_data:
            self.json_data = json.loads(input_data)
        else:
            self.json_data = None

        self.detector = detector
        self.recognizer = recognizer
        self.json_output = {}

    def set_input_data(self, input_data: InputData) -> None:
        self.json_data = json.loads(input_data)
        self.json_output = {}
    
    def get_input_data(self) -> InputData:
        return self.json_data

    def get_output_data(self) -> OutputData:
        return self.json_output
    
    def read_img(self, img_source: str, format="route") -> np.ndarray:
        if format=="route":
            img = cv2.imread(img_source)
        elif format=="b64":
            nparr = np.frombuffer( base64.b64decode(img_source) , np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            print("Format not understood")
            img = None

        return img
    
    # Process a single image
    def process_image(self, img: np.ndarray, width_divider: int = 4) -> np.ndarray:
        if img is None: return None
        
        img = imutils.resize(img, width=int(img.shape[1]/width_divider))
        bboxs, _ = self.detector.detect(img, threshold=0.5, scale=1.0)
        if( bboxs is None or len(bboxs)==0): return None
        
        todel = []
        for i in range(bboxs.shape[0]):
            if(any(x<0 for x in bboxs[i])):
                todel.append(i)
        for i in todel:
            bboxs = np.delete(bboxs, i, 0)

        m_area = 0
        id_max = 0

        for (i, bbox ) in enumerate(bboxs):
            area = (int(bbox[3]) - int(bbox[1]))*(int(bbox[2]) -int(bbox[0]))
            if(area > m_area):
                id_max = i
                m_area = area

        face = scaller_conc( img[int(bboxs[id_max][1]):int(bboxs[id_max][3]), int(bboxs[id_max][0]):int(bboxs[id_max][2]), :] )
        
        if face is None: return None
        # Returning the embedding. Returning the first element only.
        else: 
            embedding = self.recognizer.get_embedding(face)[0]
            return [ float(num) for num in embedding ]

    # Process a list of images and return a list of embeddings for a key
    def process_images(self, imgs: List[np.ndarray], key: str) -> OutputData:
        self.json_output = {}
        width_divider = 4

        # Preparing the output for a key
        embeddings = []

        # Reading the images for a key
        for i,img in enumerate(imgs):
            embedding = self.process_image(img, width_divider)
            if embedding: 
                embeddings.append( {"img":i , "embedding": embedding } )
                print(f'File completed: {i} for key {key}')
                    
            self.json_output[key] = embeddings
        
        return self.json_output

    # Process a list of images from a json. the json contains the path to the images or the base64 encoding of the images
    def process_data(self, img_reading_format: str= "route") -> OutputData:
        if img_reading_format!="route" and img_reading_format!="b64": 
            print("Format not understood")
            return "{}"

        if not self.json_data:
            print("Data empty. please set the data")
            return "{}"

        self.json_output = {}
        #self.json_output['name'] = self.json_data['name']
        #self.json_output["embeddings"] = []

        width_divider = 4
    
        keys = self.json_data.keys()

        # Processing each image for each key
        for key in keys:
            # Preparing the output for a key
            embeddings = []

            # Reading the images for a key
            for img_name in self.json_data[key]:
                print(f'Processing file: {img_name} for key {key}')
                img = self.read_img( img_name, img_reading_format)
                embedding = self.process_image(img, width_divider)
                if embedding is None: continue 
                
                embeddings.append( {"img":img_name , "embedding": embedding } )
                print(f'File completed: {img_name} for key {key}')
                    
            self.json_output[key] = embeddings
        #print(self.json_data)
        #self.json_output = embeddings
        
        return self.json_output

    @staticmethod
    def input_path_to_json(input_path: str) -> str:
        json_data = {}

        # Listing the folders. there are the labels for the images
        for folder in os.listdir(input_path):

            # ignore files at this level
            if not os.path.isdir(os.path.join(input_path, folder)):
                continue
            
            # Listing the images for each folder
            json_data[folder] = []
            for img_name in os.listdir(os.path.join(input_path, folder)):
                json_data[folder].append(os.path.join(input_path, folder, img_name))
        return str(json_data).replace("'", '"')

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input-data", required=False, help="json containing input data")
    ap.add_argument("-ip", "--input-data-path", required=False, help="Path to a folder containing input data")
    ap.add_argument("-o", "--out", required=False, help="save json containing input data")
    ap.add_argument("-p", "--print", action="store_true", help="Prints output on console")
    ap.add_argument("-dd", "--det-dev", required=False, help="Detection device to use. Default is CPU. -1 for CPU, 0-N for GPU id")
    ap.add_argument("-rd", "--rek-dev", required=False, help="Recognition device to use. Default is CPU. -1 for CPU, 0-N for GPU id")
    args = vars(ap.parse_args())

    if not args["input_data"] and not args["input_data_path"]:
        print("Please provide input data or input data path")
        sys.exit()

    # If the user provided a path to a folder containing the input data, convert it to json format
    if args["input_data_path"]:
        args["input_data"] = encoderExtractor.input_path_to_json(args["input_data_path"])
        print(args["input_data"])

    # Check if the user provided a valid device id
    try:
        detection_using_cpu = int(args["det_dev"]) if args["det_dev"] else -1
        rekognition_using_cpu = int(args["rek_dev"]) if args["rek_dev"] else -1
    except ValueError:
        print("Invalid device id. Must be an integer")
        sys.exit()

    print("Using CPU for detection") if detection_using_cpu == -1 else print(f"Using GPU {detection_using_cpu} for detection")
    print("Using CPU for recognition") if rekognition_using_cpu == -1 else print(f"Using GPU {rekognition_using_cpu} for recognition")

    input_data = args['input_data']
    #input_data = '{"name":"what", "img_format": "route","imgs":["imgs/felipe1.jpg","imgs/felipe7.jpg"]}'
    #input_data = '{"felipe":["imgs/felipe/felipe1.jpg","imgs/felipe/felipe7.jpg"], "vincent":["imgs/vincent/00000002.jpg","imgs/vincent/00000024.jpg"]}'
    #input_data = '{"felipe":["imgs/felipe/felipe1.jpg","imgs/felipe/felipe7.jpg"]]}'
    output = args['out']

    #loading the face detection model. 0 means to work with GPU. -1 is for CPU.
    detector = insightface.model_zoo.get_model('retinaface_r50_v1')
    detector.prepare(ctx_id = detection_using_cpu, nms=0.4)

    #loading the face recognition model. 0 means to work with GPU. -1 is for CPU.
    recognizer = insightface.model_zoo.get_model('arcface_r100_v1')
    recognizer.prepare(ctx_id = rekognition_using_cpu)

    encoder = encoderExtractor(input_data, detector, recognizer)
    result = encoder.process_data()

    if(output):
        with open(output, 'w') as outfile:
            json.dump( result, outfile)

    if args['print']:
        print("[OUTPUT:BEGIN]")
        print(json.dumps(result) )
        print("[OUTPUT:END]")
        
if __name__ == "__main__":
    main()