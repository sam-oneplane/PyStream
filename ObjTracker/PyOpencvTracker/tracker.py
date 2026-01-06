import math

class Tracker:
    
    def __init__(self) -> None:
        self.centroids =  {} # item = id : (x,y,w,h))
        self.idCounter = 0

    def update(self, objects) -> dict:

        refreshCentroids = {} # id : (x,y,w,h)
        updateCentroidsIds = []

        def detectObj(object: tuple) -> tuple:
            (x,y,w,h)  = object
            X = (x + (x+w))//2
            Y = (y + (y+h))//2
            maxEucDist = max(w, h)
            isSameObj = False
            eucledianDist = 0
            retId = None
            for objId, (x0,y0,w0,h0) in self.centroids.items():
                # calculate euclidean distance sqrt(X^2 + Y^2)
                X0 = (x0 + (x0+w0))//2
                Y0 = (y0 + (y0+h0))//2 
                eucledianDist = math.hypot(X-X0, Y-Y0)
                if eucledianDist < maxEucDist:
                    isSameObj = True
                    retId = objId
                     # keep the largest rectangle
                    if w*h < w0*h0:
                        object = (x0,y0,w0,h0)
                    break
            print(f'ID: {retId}, EUC: {eucledianDist}, MaxDistM: {maxEucDist}')
            return isSameObj, retId
        
        
        for object in objects:
            # if no detection founds create new centroid and update id counter
            isDetected, id = detectObj(object)
            if isDetected:
                refreshCentroids[id] = object
            else: # not detected    
                refreshCentroids[self.idCounter] = object
                self.idCounter+= 1

        self.centroids = refreshCentroids.copy()
        return refreshCentroids
        


