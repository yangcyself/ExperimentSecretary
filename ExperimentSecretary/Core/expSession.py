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
    columnFuncs = {}
    def  __init__(self,basedir = '.'):
        self.basedir = basedir
        
    class decoraGen:
        def __get__(self, obj, objtype):
            class Decorator:
                def __init__(self,f):
                    self.f = f
                    lst = objtype.columnFuncs.get(objtype,[])
                    lst.append(self.f)
                    objtype.columnFuncs[objtype] = lst
                    setattr(objtype,f.__name__,f)

                def __get__(self, obj, objtype):
                    return self.f
            return Decorator
    
    column = decoraGen()

    def Getcolumns(self):
        return {f.__name__:f(self)
            for k in self.columnFuncs.keys() if isinstance(self,k) for f in self.columnFuncs[k]}
            
    def body(self):
        self._res = os.listdir(".")

    def __call__(self):
        """
        The main body of a experiment
        """
        # call the body
        self.body()

        # record the experiment
        cols = self.Getcolumns()

        # json.dumps(anObject, default=json_util.default)
        # json.loads(aJsonString, object_hook=json_util.object_hook)
        
        os.makedirs(os.path.join(self.basedir,".exps"),exist_ok=True)
        # print(json.dumps(cols,default=json_util.default))
        with open(os.path.join(self.basedir,".exps", datetime.now().strftime("%Y-%m-%d-%H_%M_%S.json")),"w") as f:
            json.dump(cols,f,default=json_util.default)
    
class Session(Session_t):
    """
    The most basic fields an experiment
    """

    def __init__(self):
        super().__init__()

    @Session_t.column
    def date_time(self):
        return datetime.now()

    @Session_t.column
    def git_version(self):
        # git log --pretty=format:'%H' -n 1
        repo = Repo(os.path.dirname(os.path.abspath(__file__)),search_parent_directories=True)
        headcommit = repo.head.commit
        return headcommit.hexsha

    @Session_t.column
    def res(self):
        return self._res


if __name__ == '__main__':
    s = Session()
    s()
    # print(time.time())
    