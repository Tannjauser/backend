import random
class ClassificationColor:

    def __init__(self):
        self.map = {}
        self.map.update({0: [82, 82, 82]})
        self.map.update({1: [183, 183, 183]})
        self.map.update({2: [138, 80, 55]})
        self.map.update({3: [30, 123, 18]})
        self.map.update({4: [47, 187, 29]})
        self.map.update({5: [67, 248, 44]})
        self.map.update({6: [61, 161, 208]})
        self.map.update({7: [255, 44, 22]})
        self.map.update({8: [255, 236, 0]})
        self.map.update({9: [0, 138, 229]})

    def getColor(self, key):
        if(self.map.get(key) is None):
            self.map.update({key: [random.randint(0,255),random.randint(0,255),random.randint(0,255)]})
        return self.map.get(key)