import numpy as np
import laspy
import json
import os

class Point:
    """A point located at (x,y) in 2D space.

    Each Point object may be associated with a payload object.

    """

    def __init__(self, x, y, z,classification, intensity, rgb):
        self.x, self.y , self.z= x, y, z
        self.classification = classification
        self.intensity = intensity
        self.rgb= rgb

    def __repr__(self):
        return '{}: {}'.format(str((self.x, self.y, self.z)), repr(self.payload))
    def __str__(self):
        return 'P({:.2f}, {:.2f})'.format(self.x, self.y)

    def distance_to(self, other):
        try:
            other_x, other_y = other.x, other.y
        except AttributeError:
            other_x, other_y = other
        return np.hypot(self.x - other_x, self.y - other_y)

class Chunck:
    """A rectangle centred at (cx, cy) with width w and height h."""

    def __init__(self, cx, cy, w, h):
        self.cx, self.cy = cx, cy
        self.w, self.h = w, h
        self.west_edge, self.east_edge = cx - w/2, cx + w/2
        self.north_edge, self.south_edge = cy - h/2, cy + h/2

    def __repr__(self):
        return str((self.west_edge, self.east_edge, self.north_edge,
                self.south_edge))

    def contains(self, point):
        """Is point (a Point object or (x,y) tuple) inside this Chunck?"""

        try:
            point_x, point_y = point.x, point.y
        except AttributeError:
            point_x, point_y = point

        return (point_x >= self.west_edge and
                point_x <  self.east_edge and
                point_y >= self.north_edge and
                point_y < self.south_edge)

    def intersects(self, other):
        """Does Chunck object other interesect this Chunck?"""
        return not (other.west_edge > self.east_edge or
                    other.east_edge < self.west_edge or
                    other.north_edge > self.south_edge or
                    other.south_edge < self.north_edge)

class QuadTree:
    """A class implementing a quadtree."""

    def __init__(self, boundary, limit, xmin, ymin, zmin, outputDir, max_points=50000, level='0'):
        """Initialize this node of the quadtree.

        boundary is a Chunck object defining the region from which points are
        placed into this node; max_points is the maximum number of points the
        node can hold before it must divide (branch into four more nodes);
        level keeps track of how deep into the quadtree this node lies.

        """

        self.boundary = boundary
        self.max_points = max_points
        self.points = []
        self.level = level
        self.limit = limit
        # A flag to indicate whether this node has divided (branched) or not.
        self.divided = False
        self.notDone=True
        self.xmin=xmin
        self.ymin=ymin
        self.zmin=zmin
        self.outputDir=outputDir

    def exportData(self):
        self.getPoints(self.xmin, self.ymin, self.zmin, self.outputDir)
        del self.max_points
        if self.level != '0':
            del self.points
        del self.limit
        del self.xmin
        del self.ymin
        del self.zmin
        del self.outputDir

    def clean(self):
        del self.max_points
        if self.level != '0':
            del self.points
        del self.limit
        del self.xmin
        del self.ymin
        del self.zmin
        del self.outputDir 


    def getPoints(self, xmin, ymin, zmin, outputDir):
        returnedPoints = []
        classificationArray = []
        intensityArray = []
        rgbArray = []
        for points in self.points:
            returnedPoints.append(points.x - xmin)
            returnedPoints.append(points.z - zmin)
            returnedPoints.append(points.y - ymin)
            classificationArray.append(points.classification)
            intensityArray.append(points.intensity)
            rgbArray.append(points.rgb[0])
            rgbArray.append(points.rgb[1])
            rgbArray.append(points.rgb[2])
            rgbArray.append(points.rgb[3])
        boundary = self.getBoundary()
        boundaryArray = [boundary.cx - xmin, boundary.cy - ymin,boundary.w, boundary.h]
        if rgbArray[0] == -1:
         resultArray =  [np.array(returnedPoints).tolist(),np.array(classificationArray).tolist(), np.array(intensityArray).tolist(), boundaryArray]
        else:    
         resultArray =  [np.array(returnedPoints).tolist(),np.array(classificationArray).tolist(), np.array(intensityArray).tolist(), boundaryArray, np.array(rgbArray).tolist()]
        
        json_string = json.dumps(resultArray)
        mypath = '.'+outputDir + '/'+ self.level+'/'
        print(mypath)
        if not os.path.isdir(mypath):     
            os.makedirs(mypath)
        json_file = mypath +'data.json'
        with open(json_file, 'w') as outfile:
            outfile.write(json_string)

    def getLevel(self):
        return self.level
    
    def getBoundary(self):
        return self.boundary
    
    def isDivided(self):
        return self.divided
    
    def getAllPoints(self, points, xmin, ymin, zmin, outputDir):
        if self.notDone:
            if len(self.points) >0:
                points[self.level]=(self.getPoints(xmin, ymin, zmin,outputDir))
                self.clean()
        else:
            points[self.level]="Done"
        if self.isDivided():
            self.nw.getAllPoints(points, xmin, ymin, zmin, outputDir)
            self.ne.getAllPoints(points, xmin, ymin, zmin, outputDir) 
            self.se.getAllPoints(points, xmin, ymin, zmin, outputDir) 
            self.sw.getAllPoints(points, xmin, ymin, zmin, outputDir) 


    def divide(self):
        """Divide (branch) this node by spawning four children nodes."""

        cx, cy = self.boundary.cx, self.boundary.cy
        w, h = self.boundary.w / 2, self.boundary.h / 2
        # The boundaries of the four children nodes are "northwest",
        # "northeast", "southeast" and "southwest" quadrants within the
        # boundary of the current node.
        self.nw = QuadTree(Chunck(cx - w/2, cy - h/2, w, h), self.limit,
                                    self.xmin, self.ymin, self.zmin, self.outputDir,
                                    self.max_points, str(self.level) + str(1))
        self.ne = QuadTree(Chunck(cx + w/2, cy - h/2, w, h), self.limit,
                                    self.xmin, self.ymin, self.zmin, self.outputDir,
                                    self.max_points, str(self.level) + str(2))
        self.se = QuadTree(Chunck(cx + w/2, cy + h/2, w, h), self.limit,
                                    self.xmin, self.ymin, self.zmin, self.outputDir,
                                    self.max_points, str(self.level) + str(3))
        self.sw = QuadTree(Chunck(cx - w/2, cy + h/2, w, h), self.limit,
                                    self.xmin, self.ymin, self.zmin, self.outputDir,
                                    self.max_points, str(self.level) + str(4))
        self.divided = True

    def insert(self, point):
        """Try to insert Point point into this QuadTree."""

        if not self.boundary.contains(point):
            # The point does not lie inside boundary: bail.
            return False
        if self.notDone:
            if len(self.points) < int(self.max_points):
                # There's room for our point without dividing the QuadTree.
                self.points.append(point)
                return True

            # If the limit has been reached, insert either way.
            if len(str(self.level)) >= int(self.limit) and self.limit != -1:
                self.points.append(point)
                return True

            # No room: divide if necessary, then try the sub-quads.
            if not self.divided:
                self.divide()
                self.notDone=False
                self.exportData()

        return (self.ne.insert(point) or
                self.nw.insert(point) or
                self.se.insert(point) or
                self.sw.insert(point))


    def query(self, boundary, found_points):
        """Find the points in the quadtree that lie within boundary."""

        if not self.boundary.intersects(boundary):
            # If the domain of this node does not intersect the search
            # region, we don't need to look in it for points.
            return False

        # Search this node's points to see if they lie within boundary ...
        for point in self.points:
            if boundary.contains(point):
                found_points.append(point)
        # ... and if this node has children, search them too.
        if self.divided:
            self.nw.query(boundary, found_points)
            self.ne.query(boundary, found_points)
            self.se.query(boundary, found_points)
            self.sw.query(boundary, found_points)
        return found_points


    def query_circle(self, boundary, centre, radius, found_points):
        """Find the points in the quadtree that lie within radius of centre.

        boundary is a Chunck object (a square) that bounds the search circle.
        There is no need to call this method directly: use query_radius.

        """

        if not self.boundary.intersects(boundary):
            # If the domain of this node does not intersect the search
            # region, we don't need to look in it for points.
            return False

        # Search this node's points to see if they lie within boundary
        # and also lie within a circle of given radius around the centre point.
        for point in self.points:
            if (boundary.contains(point) and
                    point.distance_to(centre) <= radius):
                found_points.append(point)

        # Recurse the search into this node's children.
        if self.divided:
            self.nw.query_circle(boundary, centre, radius, found_points)
            self.ne.query_circle(boundary, centre, radius, found_points)
            self.se.query_circle(boundary, centre, radius, found_points)
            self.sw.query_circle(boundary, centre, radius, found_points)
        return found_points

    def query_radius(self, centre, radius, found_points):
        """Find the points in the quadtree that lie within radius of centre."""

        # First find the square that bounds the search circle as a Chunck object.
        boundary = Chunck(*centre, 2*radius, 2*radius)
        return self.query_circle(boundary, centre, radius, found_points)


    def __len__(self):
        """Return the number of points in the quadtree."""

        npoints = len(self.points)
        if self.divided:
            npoints += len(self.nw)+len(self.ne)+len(self.se)+len(self.sw)
        return npoints