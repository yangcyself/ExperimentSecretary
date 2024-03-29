"""
    An experiment session is one entry in the logging database
"""
from bson import json_util
import json
from datetime import datetime
import time
import git
from git import Repo
import os
import traceback
import platform

import sys
import io
import types


class Session_t:
    # column functions are called after each experiment(with no extra arguments)
    # its name and return value will be recorded 
    _columnFuncs = {}
    def  __init__(self,expName, basedir):
        self._basedir = basedir
        self._runtimeInfoStor = {} # The information added in runtime, added through `add_info`
        self._storFileName = datetime.now().strftime("%Y-%m-%d-%H_%M_%S")
        if(expName is not None):
            self._runtimeInfoStor["expName"] = expName
        
    class _decoraGen:
        def __get__(self, obj, objtype):
            class Decorator:
                def __init__(self,f):
                    self.f = f
                    lst = objtype._columnFuncs.get(objtype,[])
                    lst.append(self.f)
                    objtype._columnFuncs[objtype] = lst
                    setattr(objtype,f.__name__,f)

                def __get__(self, obj, objtype):
                    return self.f
            return Decorator

    # calling @SOMECLASS.column will regist the decorated function to the column list
    column = _decoraGen() 

    def _Getcolumns(self):
        return {f.__name__:f(self)
            for k in self._columnFuncs.keys() if isinstance(self,k) for f in self._columnFuncs[k]}
            
    def body(self):
        raise NotImplementedError

    def _summarise(self):
        # record the experiment
        cols = self._Getcolumns()
        cols.update(self._runtimeInfoStor)

        # json.dumps(anObject, default=json_util.default)
        # json.loads(aJsonString, object_hook=json_util.object_hook)
        
        os.makedirs(os.path.join(self._basedir,".exps"),exist_ok=True)
        # print(json.dumps(cols,default=json_util.default))
        with open(os.path.join(self._basedir,".exps", self._storFileName+".json"),"w") as f:
            json.dump(cols,f, indent = 2, default=json_util.default)
    

    def __call__(self):
        """
        The main body of a experiment
        """
        # call the body
        try:
            self.body()
            self._termination = "success"
        except Exception as ex:
            self._termination = traceback.format_exc()
            print("Termination:", self._termination)
        self._summarise()

    def add_info(self,k,v):
        """
            add infomation to `runtimeinfostor`
        """
        self._runtimeInfoStor[k] = v

    def __enter__(self):
        return self

    def __exit__(self,*ex):
        self._termination =  "success" if ex[0] is None else traceback.format_exc()
        if (ex[0] is not None):
            traceback.print_exception(*ex)
        self._summarise()

class stdLogger:
    """
        Log all the `write` and `writeLines` into a string stream
        modify the stdobj in construction, and change it back in destruction
    """
    def __init__(self, stdobj):
        self.stdobj = stdobj
        self.sys_write = stdobj.write
        self.sys_writelines = stdobj.writelines

        self.output = io.StringIO()

        def logf_write(self_, text):
            self.output.write(text)
            self.sys_write(text)
            

        def logf_writelines(self_, text):
            self.output.writelines(text)
            self.sys_writelines(text)
            
        stdobj.write = types.MethodType(logf_write, stdobj )
        stdobj.writelines = types.MethodType(logf_writelines, stdobj )

    def __del__(self):
        self.stdobj.write = types.MethodType(self.sys_write, self.stdobj )
        self.stdobj.writelines = types.MethodType(self.sys_writelines, self.stdobj )

    def getvalue(self):
        return self.output.getvalue()

class Session(Session_t):
    """
    The most basic fields an experiment
    """

    def __init__(self,expName=None, basedir = '.', terminalLog = False, **kwargs):
        """
        The init value will save all the kwargs, so that user can pass whatever he want to stor to the init of parent class
        """
        super().__init__(expName, basedir)
        self.add_info("Session Parameters",kwargs)
        
        self._git_version_ = self._git_version()
        self._init_time_ = datetime.now()
        self._git_diff_ = self._git_diff()

        self.terminalLog = terminalLog
        if(self.terminalLog):
            self.stdoutLog = stdLogger(sys.stdout)
            self.stderrLog = stdLogger(sys.stderr)

    def body(self):
        """
        An example body, override the body method to experiment specific actions
        """
        self._res = os.listdir(".")

    @Session_t.column
    def fin_time(self):
        return datetime.now()

    @Session_t.column
    def init_time(self):
        return self._init_time_

    def _git_version(self):
        repo = Repo(os.path.abspath(self._basedir),search_parent_directories=True)
        headcommit = repo.head.commit
        return headcommit.hexsha

    @Session_t.column
    def git_version(self):
        """
            store the current git commit id. 
        """
        # git log --pretty=format:'%H' -n 1
        return self._git_version_

    def _git_diff(self):
        repo = Repo(os.path.abspath(self._basedir),search_parent_directories=True)
        t = repo.head.commit.tree
        return repo.git.diff(t)

    @Session_t.column
    def git_diff(self):
        """
            store the all changes of the current commit. 
        """
        return self._git_diff_

    @Session_t.column
    def res(self):
        try:
            return self._res
        except:
            return None


    @Session_t.column
    def termination(self):
        return self._termination


    @Session_t.column
    def platform(self):
        """
        The name of the computer
        """
        return platform.node()
    
    @Session_t.column
    def stdout(self):
        return self.stdoutLog.getvalue() if self.terminalLog else None
    
    @Session_t.column
    def stderr(self):
        return self.stderrLog.getvalue() if self.terminalLog else None
    

"""
To define a column function, you can either call `@Session_t.column` inside the definition body
or call @Session.column outside of the definition body
"""

if __name__ == '__main__':
    s = Session()
    s()

    