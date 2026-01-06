import json
import os

class TrackerParams:
    def __init__(self):
        self._params = {}
        self._videoPath = None

    
    def parse(self, jsonPath: str)-> None:
        with open(jsonPath) as f:
            data = json.load(f)
            self._videoPath = data["path"]
            for entry in data["samples"]:
                key = entry["name"]
                value = entry["parameters"]
                self._params[key] = value


    def convertRoiByKey(self, key):
        if key in list(self._params.keys()):
            roiParams = self._params[key]
            roi = roiParams['FrameRoi'].split(",")
            roiParams['FrameRoi'] = tuple([int(i) for i in roi])
            return roiParams                        
        return None


    @property
    def params(self) -> dict:
        return self._params

    @property
    def path(self) -> str:
        return self._videoPath 

    @params.deleter
    def params(self) -> None:
        del self._params
    

if __name__ == "__main__":

    jsonPath = os.path.join('/','home','avivi','Developer','Python','OpenCV','video','samples_params.json')
    trcParams = TrackerParams()
    trcParams.parse(jsonPath)
    key = 'highway_1.mp4'
    
    params = trcParams.params
    path = trcParams.path
    videoPath = os.path.join(path, key)
    print(videoPath)

    roiParams = trcParams.convertRoiByKey(key)

    '''
    roiParams = params[key]
    #print(trcParams.convertRoiByKey(key))
    roi = roiParams['FrameRoi'].split(",")
    roiParams['FrameRoi'] = tuple([int(i) for i in roi])
    '''
    
    print(roiParams)

