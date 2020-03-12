import matplotlib.pyplot as plt
import numpy as np



def convertTime(timearray, zerotime = None):
    if(zerotime is None):
        zerotime = timearray[0]
    return (np.array(timearray) - zerotime)/1e6

class FMSreader:
    def __call__(self,f,msg):
        """
            f: opened file
            Use side effects to record the data read from the file
            return when the state finished, with the next state to enter, and a message to the next state
        """
        raise NotImplementedError


class readPassInit(FMSreader):
    """
    the class that goes through headning lines.
        When it meets a trigger, it calles the correspoinding reader
    """
    def __init__(self, triggers = [] ,readers = []):
        self.triggers = triggers
        self.readers = readers
    def __call__(self,f,msg):
        a = msg if (msg is not None) else f.readline()
        while(True):
            for t,r in zip(self.triggers,self.readers):
                if(t in a):
                    return r, a
            a = f.readline()
            if(a==""):
                return None, a


class readPrettyPrint(FMSreader):
    """
    the class that reads a block like.
    xxxxxxx
    -0.577775   0.223376  -0.315034   0.115284 ...
    """
    def __init__(self,stor,trigger,passreader = None):
        self.stor = stor
        self.passreader = passreader
        self.trigger = trigger
    def __call__(self,f,msg=None):
        assert(self.trigger in msg)
        a = f.readline()
        gcforce = np.fromstring(a,sep  = " ")
        self.stor(gcforce)
        return self.passreader, None


class readTimedPrettyPrint(FMSreader):
    """
    the class that reads a block like.
    xxxxxxxtime_stamp: 234567678
    xxxxxxx
    -0.577775   0.223376  -0.315034   0.115284 ...
    """
    def __init__(self,stor,trigger,passreader = None):
        self.stor = stor
        self.passreader = passreader
        self.trigger = trigger
    def __call__(self,f,msg=None):
        assert(self.trigger in msg)
        t = int(msg.strip().split(" ")[-1])
        a = f.readline()
        assert(self.trigger[:-11] in a)
        a = f.readline()
        gcforce = np.fromstring(a,sep  = " ")
        self.stor(t,gcforce)
        return self.passreader, None



class simpleVecterStor():
    """
    The stor for readPrettyPrint
    """
    def __init__(self,name,dimnames = ["x","y","z"]):
        self.stor = []
        self.name = name
        self.dimNames = dimnames
    def __call__(self,vec):
        self.stor.append(vec)
    def show(self,dims = [0,1,2],ax = None, dimnames = None, legend_title = True, timeStamps = None, func = (lambda x: x)):
        if(dimnames is None):
            dimnames = self.dimNames
        values = np.array(self.stor)
        if(ax is None):
            ax = plt.gca()
        for d in np.array(dims).reshape(-1):
            try:
                ax.plot(timeStamps,func(values[:,d]),label = dimnames[d])
            except ValueError as ex:
                ax.plot(func(values[:,d]),label = dimnames[d])
                
        if(legend_title):
            ax.legend()
            plt.title(self.name)
        return ax
    
    def show2d(self, xdim, ydim, ax = None, label = None):
        values = np.array(self.stor)
        if(ax is None):
            ax = plt.gca()
        ax.plot(values[:,xdim], values[:,ydim],label = label)
        return ax

    def show3d(self, xdim, ydim, zdim = None, ax = None, label = None):
        values = np.array(self.stor)
        if(ax is None):
            ax = plt.add_subplot(111, projection='3d') 
        zvalue = values[:,zdim]
        ax.plot(values[:,xdim], values[:,ydim], zvalue , label = label)
        return ax


class simpleTimedVecterStor(simpleVecterStor):
    """
    The stor for readTimedPrettyPrint
    """
    def __init__(self,name,dimnames = ["x","y","z"]):
        super().__init__(name,dimnames)
        self.timeStamps = []
    
    def __call__(self,t,vec):
        super().__call__(vec)
        self.timeStamps.append(t)

    def show(self,dims = [0,1,2],ax = None, legend_title = True, zerotime = None):
        return super().show(dims = dims, ax = ax, legend_title = legend_title, 
            timeStamps=convertTime(self.timeStamps,zerotime))
        

#############################################################################
##################  PARSERS #################################################
#############################################################################

class Parsser:
    """
    The log parser for processing the experiments
        When called, it calls its readers one by one according to the FSM transition rule
    """
    def __init__(self,MPCstor,WBCstor):
        self.passreader = readPassInit()
        self.passreader.triggers = []
        self.passreader.readers = []
        self.readerPtr = self.passreader

    def addVecParser(self,trigger,name,dimnames = ["x","y","z"],parsType = readPrettyPrint):
        stor = simpleVecterStor(name,dimnames)
        pars = parsType(stor,trigger,self.passreader)
        self.passreader.triggers.append(trigger)
        self.passreader.readers.append(pars)
        return stor

    def addTimedVecParser(self,trigger,name,dimnames = ["x","y","z"],parsType = readTimedPrettyPrint):
        stor = simpleTimedVecterStor(name,dimnames)
        pars = parsType(stor,trigger,self.passreader)
        self.passreader.triggers.append(trigger)
        self.passreader.readers.append(pars)
        return stor

    def __call__(self,f):
        msg = None
        while(True):
            try:
                self.readerPtr, msg =  self.readerPtr(f,msg)
            except TypeError as ex:
                if(str(ex) == "'NoneType' object is not callable"):
                    break
                else:
                    raise ex

"""
# An example of experiment Class

class experiment:
    def __init__(self,simlog, ctrllog, name = "exp"):
        self.simustor = simuReactionForceStor()
        self.simloger = simLogPasser(self.simustor)
        with open(simlog,"r") as f:
            self.simloger(f)

        self.wbcstor = WBICSolutionFrStor()
        self.mpcstor = CMPCDesiredFrStor()
        self.ctrlloger = ctrlLogPasser(self.mpcstor,self.wbcstor)
        self.posErrorStor = self.ctrlloger.addVecParser("HL_PID_PositionError","pos Error")
        self.velStor = self.ctrlloger.addVecParser("HL_PID_woldVelocity","vel")
        with open(ctrllog,"r") as f:
            self.ctrlloger(f)
        self.indmap = [9,11,13,15]
        self.name = name

    def getxlim(self):
        return ( min([x[0] for x in list(self.wbcstor.gcStor.values())[0]]) , max([x[0] for x in list(self.wbcstor.gcStor.values())[0]]))

    def showHLpid(self,dims = [0,1,2]):
        self.posErrorStor.show(dims)
        plt.show()
        self.velStor.show(dims)
        plt.show()
"""