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


class Session_t:
    # column functions are called after each experiment(with no extra arguments)
    # its name and return value will be recorded 
    _columnFuncs = {}
    def  __init__(self,expName, basedir):
        self._basedir = basedir
        self._runtimeInfoStor = {} # The information added in runtime, added through `add_info`
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
        with open(os.path.join(self._basedir,".exps", datetime.now().strftime("%Y-%m-%d-%H_%M_%S.json")),"w") as f:
            json.dump(cols,f,default=json_util.default)
    

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


class Session(Session_t):
    """
    The most basic fields an experiment
    """

    def __init__(self,expName=None, basedir = '.'):
        super().__init__(expName, basedir)

    def body(self):
        """
        An example body, override the body method to experiment specific actions
        """
        self._res = os.listdir(".")

    @Session_t.column
    def date_time(self):
        return datetime.now()

    @Session_t.column
    def git_version(self):
        """
            store the current git commit id. 
        """
        # git log --pretty=format:'%H' -n 1
        repo = Repo(os.path.abspath(self._basedir),search_parent_directories=True)
        headcommit = repo.head.commit
        return headcommit.hexsha


    @Session_t.column
    def git_diff(self):
        """
            store the all changes of the current commit. 
        """
        repo = Repo(os.path.abspath(self._basedir),search_parent_directories=True)
        t = repo.head.commit.tree
        return repo.git.diff(t)



    @Session_t.column
    def res(self):
        try:
            return self._res
        except:
            return None


    @Session_t.column
    def termination(self):
        return self._termination


"""
To define a column function, you can either call `@Session_t.column` inside the definition body
or call @Session.column outside of the definition body
"""

if __name__ == '__main__':
    s = Session()
    s()

    