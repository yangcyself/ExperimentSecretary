import matplotlib.pyplot as plt
import numpy as np
import re


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
    def __init__(self, triggers = None ,readers = None):
        self.triggers = triggers if (triggers is not None) else []
        self.readers = readers if (readers is not None) else []
    def __call__(self,f,msg):
        a = msg if (msg is not None) else f.readline()
        while(True):
            for t,r in zip(self.triggers,self.readers):
                if(t in a):
                    return r, a
            a = f.readline()
            if(a==""):
                return None, a


class readVector(FMSreader):
    """
    the class that provides functions to read a vector (this is still a virtual class)
        Vector form can be:
        numpy style closed by '[]' with linebreaks in it.
            [ 1.66666667 -1.     (\n)    -1.66666667  3.        ] 
        simply no brakes

    we assume that each reader have one const form of vectors, thus this class first try these forms and set 
    to one of them once decided in the first call.
    I think this will be faster than using if in every iteration
    """
    def __init__(self,sep  = ' '):
        self.readvector = self.readfunc0
        self.sep = sep


    def readfunc0(self,f,msg):
        """
        the init func to be called, which tries each form and set the `self.readvector`
        msg should be the vector or the first line of the vector if it has linebreaks
        """
        try:
            # vecstr = msg[msg.index('[')+1:]
            vec = self.readfuncNPStyle(f,msg)
            self.readvector = self.readfuncNPStyle
        except ValueError as ex: 
            vec = self.readfuncNoBrackets(f,msg)
            self.readvector = self.readfuncNoBrackets
        return vec


    def readfuncNPStyle(self, f,msg):
        vecstr = msg[msg.index('[')+1:]
        try: # put reading the first line in `try` because I think printing a short vector is the most common case
            vecstr = vecstr[:vecstr.index(']')]
        except ValueError as ex: 
            assert("substring not found") in str(ex)
            a = f.readline()
            while (']' not in a):
                vecstr += " " + a.strip()
            vecstr += " " + a[:vecstr.index(']')]
        return np.fromstring(vecstr, sep = self.sep)
    

    def readfuncNoBrackets(self, f,msg):
        return np.fromstring(msg.strip(), sep = self.sep)

            
class readPrettyPrint(readVector):
    """
    the class that reads a block like.
    xxxxxxx
    -0.577775   0.223376  -0.315034   0.115284 ...
    """
    
    def __init__(self,stor,trigger,passreader = None):
        super().__init__()
        self.stor = stor
        self.passreader = passreader
        self.trigger = trigger
    def __call__(self,f,msg=None):
        msg = f.readline() if (msg is None) else msg
        assert(self.trigger in msg)
        a = f.readline()
        vec = self.readvector(f,a)
        self.stor(vec)
        return self.passreader, None


class readOnelineVector(readVector):
    """
    the class that reads a block like.
    xxxxxxx [-0.577775   0.223376  -0.315034   0.115284]
    Note: if there is no brackts, the array should just follows the trigger
    """
    def __init__(self,stor,trigger, passreader = None, sep = ' '):
        super().__init__(sep = sep)
        self.stor = stor
        self.passreader = passreader
        self.trigger = trigger
        self.sep  = sep
    
    def __call__(self,f,msg=None):
        msg = f.readline() if (msg is None) else msg
        assert(self.trigger in msg)
        vec = self.readvector(f,msg[len(self.trigger):])
        self.stor(vec)
        return self.passreader, None


class readTimedPrettyPrint(readVector):
    """
    the class that reads a block like.
    xxxxxxxtime_stamp: 234567678
    xxxxxxx
    -0.577775   0.223376  -0.315034   0.115284 ...
    """
    def __init__(self,stor,trigger,passreader = None):
        super().__init__()
        self.stor = stor
        self.passreader = passreader
        self.trigger = trigger
    def __call__(self,f,msg=None):
        msg = f.readline() if (msg is None) else msg
        assert(self.trigger in msg)
        t = int(msg.strip().split(" ")[-1])
        a = f.readline()
        assert(self.trigger[:-11] in a)
        a = f.readline()
        vec = self.readvector(f,a)
        self.stor(t,vec)
        return self.passreader, None


class readRegularExpression(FMSreader):
    """
    The class that read a regular expression
        It calls `findall` of a regular expression and pass the result directly to stor
    And the reader will keep on reading until the findall finally matches something
    """
    def __init__(self,stor,trigger,rgex=r"(.*)",passreader = None):
        super().__init__()
        self.stor = stor
        self.passreader = passreader
        self.trigger = trigger
        self.rgex = rgex

    def __call__(self,f,msg=None):
        msg = f.readline() if (msg is None) else msg
        res = re.findall(self.rgex, msg)
        while(not len(res)):
            msg = f.readline()
            res = re.findall(self.rgex, msg)
        self.stor(res)
        return self.passreader, None


#############################################################################
################## Stor #################################################
#############################################################################

class simpleStor():
    """
    This is just a list with stor's interface
    """
    def __init__(self,name):
        self.stor = []
        self.name = name
    
    def __call__(self,item):
        self.stor.append(item)
    
    def clear(self):
        self.stor = []

class simpleVecterStor(simpleStor):
    """
    The stor for readPrettyPrint
    """
    def __init__(self,name,dimnames = ["x","y","z"]):
        super().__init__(name)
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
    
    def clear(self):
        super().clear()
        self.timeStamps = []


#############################################################################
##################  PARSERS #################################################
#############################################################################

class Parsser:
    """
    The log parser for processing the experiments
        When called, it calls its readers one by one according to the FSM transition rule
    """
    def __init__(self):
        self.passreader = readPassInit()
        self.readerPtr = self.passreader

    def __call__(self,f,msg = None):
        while(True):
            try:
                self.readerPtr, msg =  self.readerPtr(f,msg)
            except TypeError as ex:
                if(str(ex) == "'NoneType' object is not callable"):
                    break
                else:
                    raise ex
        return msg

class TriggerParsser(Parsser):
    """
        A parsser drived by triggers
    """
    def __init__(self):
        super().__init__()
        self.passreader.triggers = []
        self.passreader.readers = []

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


class SequenceParsser(Parsser):
    """
        A parser drived by reading in sequence
    """
    def __init__(self,trigger = None, readers = None):
        super().__init__()
        self.readers = readers if (readers is not None) else [] # Note! this readers.copy is very important, otherwise even not passing this parameter, the reader still not get correctly initiallized
        if(trigger is not None):
            self.passinit = readPassInit(triggers=[trigger],readers=[None])
        else:
            self.passinit = lambda a,b: None,None # do not wait for a trigger
        # hack the self.readerPrt so that the reader starts from the first item of readers
        # self.readerPtr = lambda f,msg: self.readers[0],None 

    def addVecParser(self,trigger,name,dimnames = ["x","y","z"],parsType = readPrettyPrint):
        stor = simpleVecterStor(name,dimnames)
        pars = parsType(stor,trigger,None)
        self.readers.append(pars)
        return stor
    
    def addItemParser(self,trigger,name, parsType = readRegularExpression, **kwarg):
        stor = simpleStor(name)
        pars = parsType(stor,trigger, passreader= None, **kwarg)
        self.readers.append(pars)
        return stor
    

    def __call__(self, f, msg = None):
        _, msg = self.passinit(f,msg)
        while(True):
            msg = f.readline() if(msg is None) else msg
            if(self.readers[0].trigger in msg):
                for r in self.readers:
                    _, msg =  r(f,msg)    
            else:
                return msg
    


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

"""
Another example

class readLSE(LogParser.readVector):
    " " "
        read a block like 
        initState: [-3. -3. -3. -3.]
         ....... Many lines of .........
         ....... moved Points: xxxx xxxx ......
         ....... its Cl and Cu: xxxx xxxx ......
         
    " " "
    def __init__(self, stor, trigger,passreader = None):
        super().__init__()
        self.stor = stor
        self.classifyParser = LogParser.SequenceParsser(trigger ="moved Points:" )
        
        self.classifiedPointStor = self.classifyParser.addVecParser("moved Points:","classified_Point",parsType = LogParser.readOnelineVector)
        self.classifiedBoundStor = self.classifyParser.addVecParser("its Cl and Cu:","classified_Bound",parsType =LogParser.readOnelineVector)
        
        self.passreader = passreader
        self.trigger = trigger
        
    def __call__(self,f,msg=None):
        assert(self.trigger in msg)
        vec = self.readvector(f,msg[len(self.trigger):])
        self.classifyParser(f)
        self.stor((vec,self.classifiedPointStor.stor.copy(), self.classifiedBoundStor.stor.copy()))
        self.classifiedPointStor.stor.clear() 
        self.classifiedBoundStor.stor.clear()
        return self.passreader, None



class experiment:
    def __init__(self,log, name = "exp"):
        self.parsser = LogParser.TriggerParsser()
        self.stor  = LogParser.simpleStor(name="LSE data")
        trigger = "initState:"
        pars = readLSE(self.stor,trigger,self.parsser.passreader)
        self.parsser.passreader.triggers.append(trigger)
        self.parsser.passreader.readers.append(pars)

        with open(log,"r") as f:
            self.parsser(f)

    def show(self, iterations = 50):
        slctP = np.array([s[0] for s in self.stor.stor[:iterations]])
        plt.plot(slctP[:,0],slctP[:,1],'x')
        clsfP = np.array([v for s in self.stor.stor[:iterations] for v in s[1]])

        plt.plot(clsfP[:,0],clsfP[:,1],'.')
        plt.show()
        
"""