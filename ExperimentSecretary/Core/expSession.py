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

class Session_t:
    # column functions are called after each experiment(with no extra arguments)
    # its name and return value will be recorded 
    _columnFuncs = {}
    def  __init__(self,basedir = '.'):
        self._basedir = basedir
        
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

    def __call__(self):
        """
        The main body of a experiment
        """
        # call the body
        self.body()

        # record the experiment
        cols = self._Getcolumns()

        # json.dumps(anObject, default=json_util.default)
        # json.loads(aJsonString, object_hook=json_util.object_hook)
        
        os.makedirs(os.path.join(self._basedir,".exps"),exist_ok=True)
        # print(json.dumps(cols,default=json_util.default))
        with open(os.path.join(self._basedir,".exps", datetime.now().strftime("%Y-%m-%d-%H_%M_%S.json")),"w") as f:
            json.dump(cols,f,default=json_util.default)
    

class Session(Session_t):
    """
    The most basic fields an experiment
    """

    def __init__(self):
        super().__init__()

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
        # git log --pretty=format:'%H' -n 1
        repo = Repo(os.path.dirname(os.path.abspath(self._basedir)),search_parent_directories=True)
        headcommit = repo.head.commit
        return headcommit.hexsha


    @Session_t.column
    def git_diff(self):
        repo = Repo(os.path.dirname(os.path.abspath(self._basedir)),search_parent_directories=True)
        t = repo.head.commit.tree
        return repo.git.diff(t)


    @Session_t.column
    def res(self):
        return self._res


"""
To define a column function, you can either call `@Session_t.column` inside the definition body
or call @Session.column outside of the definition body
"""

if __name__ == '__main__':
    s = Session()
    s()

    