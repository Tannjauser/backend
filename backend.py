import laspy
import numpy as np  

import inspect
import warnings
import argparse
import sys
from pathlib import Path
from typing import List
from typing import Optional
from pathlib import Path
from QuadTree import *
from ClassificationColor import *
import json
import shutil
import threading
import gc

def delete_files_in_directory(directory_path):
   file_path = "."+directory_path+"/"
   try:
     shutil.rmtree(file_path)
     print("Todos los archivos de {file_path} fueron eliminados .////////////")
   except Exception as e:
     print("Error al eliminar los archivos del directorio {file_path}.")
     print(e)


def convertLAS():
    print("Adaptando el archivo LAS")
    warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)
    parser = argparse.ArgumentParser(
        "Divisor de archivos LAS", description="Transforma el archivo LAS en varios archivos para su lectura óptima"
    )
    parser.add_argument("input_file",default='./visorwebdepuntos/src/data/000029-buildings.las')
    parser.add_argument("output_dir", default='/visorwebdepuntos/public/chuncks')
    parser.add_argument("output_only_0chunck_dir", default='/visorwebdepuntos/src/data/chuncks')
    args = parser.parse_args()
    with laspy.open(args.input_file)as file:
        print("Limpiando directorios")
        delete_files_in_directory(args.output_dir)
        delete_files_in_directory(args.output_only_0chunck_dir)
        count = 0
        midpointLengthX = file.header.x_max - file.header.x_min
        midpointLengthY = file.header.y_max - file.header.y_min
        centerPositionX = file.header.x_max - midpointLengthX/2
        centerPositionY = file.header.y_max - midpointLengthY/2
        MainChunk = Chunck(centerPositionX, centerPositionY, midpointLengthX, midpointLengthY)
        quadTree = QuadTree(MainChunk,6,file.header.x_min, file.header.y_min, file.header.z_min,args.output_dir,50000)
        classificationColor=ClassificationColor()
        totalPoints = round(file.header.point_count)
        '''
        pointsToSkip = round(totalPoints/50000)
        '''
        pointsToSkip = max(1, totalPoints // 50000)
        counter=0
        print(f"Iniciando el Quadtree")
        for firstPoints in file.chunk_iterator(pointsToSkip):
            print(f"{count / file.header.point_count * 100}%")
            x, y, z, intensity, classification  = firstPoints.x.copy(), firstPoints.y.copy(), firstPoints.z.copy(), firstPoints.intensity.copy(), firstPoints.classification.copy()
            hasRgb = hasattr(firstPoints, 'red') and hasattr(firstPoints, 'green') and hasattr(firstPoints, 'blue')
            if hasRgb:
             red, green, blue=firstPoints.red.copy(), firstPoints.green.copy(), firstPoints.blue.copy() 
             quadTree.insert(Point(x[0],y[0],z[0],classification[0],intensity[0], [normalize_to_uint8(red[0]),normalize_to_uint8(green[0]), normalize_to_uint8(blue[0]),normalizeIntensity_to_uint8(intensity[0])]))
            else:
             quadTree.insert(Point(x[0],y[0],z[0],classification[0],intensity[0], [-1,-1, -1,-1]))
            count+=len(firstPoints)
            counter+=1
        print(counter)
       
        data = laspy.read(args.input_file)
        xArray, yArray, zArray, intensityArray, classificationArray = data.x.copy(), data.y.copy(), data.z.copy(), data.intensity.copy(), data.classification.copy()
        if hasRgb:
         red, green, blue=data.red.copy(), data.green.copy(), data.blue.copy() 
        else:
         red,green,blue=-1,-1,-1   
        count=0
        foward=0
        i=0
        step = max(1, totalPoints // 50000)
        threads = []
        print(f"Rellenando el QuadTree")
        while count < len(xArray):
            print(f"{count / file.header.point_count * 100}%") 
            t = threading.Thread(target=insertPoints,args=[totalPoints, xArray, yArray, zArray, intensityArray, classificationArray,classificationColor,quadTree,step,i, red, green, blue, hasRgb])
            t.start()
            t.join()
            gc.collect()
            '''
            while i < totalPoints:
                x, y, z, intensity, classification = xArray[i], yArray[i], zArray[i], intensityArray[i], classificationArray[i]
                cRGB = classificationColor.getColor(classification)
                quadTree.insert(Point(x,y,z,cRGB[0]/255,cRGB[1]/255,cRGB[2]/255,intensity/5000))
                i = i + step
            '''
            count = count + 50000
            foward+=1
            i=0 + foward
        chunckPoints = {}
        quadTree.getAllPoints(chunckPoints , file.header.x_min, file.header.y_min, file.header.z_min,args.output_dir)
        quadTree.getPoints(file.header.x_min, file.header.y_min, file.header.z_min,args.output_only_0chunck_dir)
        print(len(chunckPoints))
        

        '''
        for chunck in chunckPoints:
            json_string = json.dumps(chunckPoints[chunck])
            json_file = args.output_dir + '/'+ chunck +'.json'
            with open(json_file, 'w') as outfile:
                outfile.write(json_string)
        '''
            
        '''
        writers: List[Optional[laspy.LasWriter]] = [None] * len(chunckPoints)
        try:
            count = 0
            for pointChunck in chunckPoints:
                print(f"{count / len(chunckPoints)* 100}%")
                print(pointChunck)
                points = chunckPoints[pointChunck]
                # For performance we need to use copy
                # so that the underlying arrays are contiguous
                
                if writers[i] is None:
                    output_path = Path(sys.argv[2]) / f"{pointChunck}.las"
                    writers[i] = laspy.open(
                        output_path, mode="w", header=file.header
                    )
                writers[i].write_points(points.payload)
                count += len(points)
            print(f"{count / len(chunckPoints) * 100}%")
        finally:
            for writer in writers:
                if writer is not None:
                    writer.close()

'''
# Usage
directory_path = './visorwebdepuntos/public/chuncks'

def insertPoints(totalPoints, xArray, yArray, zArray, intensityArray, classificationArray,classificationColor,quadTree,step,i,redArray,greenArray,blueArray,hasRgb):
   while i < totalPoints:
        x, y, z, intensity, classification = xArray[i], yArray[i], zArray[i], intensityArray[i], classificationArray[i]
        if hasRgb:
         red=redArray[i]
         green=greenArray[i]
         blue=blueArray[i]
         quadTree.insert(Point(x,y,z,classification,intensity, [normalize_to_uint8(red), normalize_to_uint8(green), normalize_to_uint8(blue),normalizeIntensity_to_uint8(intensity)]))
        else:
         quadTree.insert(Point(x,y,z,classification,intensity, [-1,-1,-1,-1]))
        i = i + step


# Function to normalize uint16 values to uint8
def normalize_to_uint8(value):
    return int((value / 65536) * 255)
# Function to normalize uint16 values to uint8
def normalizeIntensity_to_uint8(value):
    return int((value / 2**8)*255)


convertLAS()

'''
def helloWorld():
    print("Hello world")
    parser = argparse.ArgumentParser(
        "LAS recursive splitter", description="Splits a las file bounds recursively"
    )
    parser.add_argument("input_file",default='./visorwebnubepuntos/src/data/000018-buildings.las')
    parser.add_argument("output_dir", default='./visorwebnubepuntos/src/data/chuncks')
    parser.add_argument("size", type=tuple_size, help="eg: 50x64.17", default='50x56')
    parser.add_argument("--points-per-iter", default=10**6, type=int)

    args = parser.parse_args()
    with laspy.open(args.input_file) as file:
        sub_bounds = recursive_split(
            file.header.x_min,
            file.header.y_min,
            file.header.x_max,
            file.header.y_max,
            args.size[0],#Tamaño 1
            args.size[1],#Tamaño 2
        )
        writers: List[Optional[laspy.LasWriter]] = [None] * len(sub_bounds)
        try:
            count = 0
            for points in file.chunk_iterator(args.points_per_iter):
                print(f"{count / file.header.point_count * 100}%")

                # For performance we need to use copy
                # so that the underlying arrays are contiguous
                x, y = points.x.copy(), points.y.copy()

                point_piped = 0

                for i, (x_min, y_min, x_max, y_max) in enumerate(sub_bounds):
                    mask = (x >= x_min) & (x <= x_max) & (y >= y_min) & (y <= y_max)

                    if np.any(mask):
                        if writers[i] is None:
                            output_path = Path(sys.argv[2]) / f"output_{i}.las"
                            writers[i] = laspy.open(
                                output_path, mode="w", header=file.header
                            )
                        sub_points = points[mask]
                        writers[i].write_points(sub_points)

                    point_piped += np.sum(mask)
                    if point_piped == len(points):
                        break
                count += len(points)
            print(f"{count / file.header.point_count * 100}%")
        finally:
            for writer in writers:
                if writer is not None:
                    writer.close()
        
    return jsonify({"x":abs( file.header.x_min-file.header.x_max),
            "y":abs(file.header.y_min-file.header.y_max)})


def recursive_split(x_min, y_min, x_max, y_max, max_x_size, max_y_size):
    x_size = x_max - x_min
    y_size = y_max - y_min

    if x_size > max_x_size:
        left = recursive_split(
            x_min, y_min, x_min + (x_size // 2), y_max, max_x_size, max_y_size
        )
        right = recursive_split(
            x_min + (x_size // 2), y_min, x_max, y_max, max_x_size, max_y_size
        )
        return left + right
    elif y_size > max_y_size:
        up = recursive_split(
            x_min, y_min, x_max, y_min + (y_size // 2), max_x_size, max_y_size
        )
        down = recursive_split(
            x_min, y_min + (y_size // 2), x_max, y_max, max_x_size, max_y_size
        )
        return up + down
    else:
        return [(x_min, y_min, x_max, y_max)]


def tuple_size(string):
    try:
        return tuple(map(float, string.split("x")))
    except:
        raise ValueError("Size must be in the form of numberxnumber eg: 50.0x65.14")

'''

