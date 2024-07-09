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
    args = parser.parse_args()
    with laspy.open(args.input_file)as file:
        print("Limpiando directorios")
        delete_files_in_directory(args.output_dir)
        count = 0
        midpointLengthX = file.header.x_max - file.header.x_min
        midpointLengthY = file.header.y_max - file.header.y_min
        centerPositionX = file.header.x_max - midpointLengthX/2
        centerPositionY = file.header.y_max - midpointLengthY/2
        MainChunk = Chunck(centerPositionX, centerPositionY, midpointLengthX, midpointLengthY)
        quadTree = QuadTree(MainChunk,6,file.header.x_min, file.header.y_min, file.header.z_min,args.output_dir,50000)
        classificationColor=ClassificationColor()
        totalPoints = round(file.header.point_count)
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
            count = count + 50000
            foward+=1
            i=0 + foward
        chunckPoints = {}
        quadTree.getAllPoints(chunckPoints , file.header.x_min, file.header.y_min, file.header.z_min,args.output_dir)
        print(len(chunckPoints))

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


def normalize_to_uint8(value):
    return int((value / 65536) * 255)
def normalizeIntensity_to_uint8(value):
    return int((value / 2**8)*255)


convertLAS()

