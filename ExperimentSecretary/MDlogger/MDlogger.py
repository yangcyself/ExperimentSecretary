import matplotlib.pyplot as plt
import time 
import os


def figOutputer(func,**outKwarg):
    """
        A function decorator for functions that calls matplotlib to output a figure. 
    """
    def wrap_func(*args, savepath = None,doc = None,show = True, **kwargs):
        res = func(*args,**kwargs)
        if(savepath is not None):
            if ("." not in savepath): # the save path is not a file name, it is a path name
                os.makedirs(savepath, exist_ok=True)
                try:
                    plt.savefig(os.path.join(savepath,"{}.png".format(kwargs["title"])))
                except:
                    plt.savefig(os.path.join(savepath,"{}.png".format(int(time.time()*10))))
            else:
                plt.savefig(savepath)
        if(doc is not None):
            if(savepath is None):
                doc.addplt()
            else:
                doc.addplt(savepath)
        if(show):
            plt.show()
        else:
            plt.clf()
        return res
    return wrap_func

class DocItem:
    def write(self):
        raise NotImplementedError

class Docfig(DocItem):
    def __init__(self, filename, title=""):
        self.filename = filename
        self.title = title
    def write(self):
        return "\n![{}]({})\n".format(self.title,self.filename)

class Docparagraph(DocItem):
    def __init__(self, content):
        self.content = content
    def write(self):
        return "\n{}\n".format(self.content)


class Doc:
    """
    use the class to record the items that we want to generate
    basic usage:
        doc = Doc()
        plt.plot(......)
        doc.addplt("figure name") # save the figure into img folder
        doc.generate() # generate corresponding Markdown paragraph
    """
    def __init__(self, logDir = "../experiment_results", filename="log_"+time.strftime("%m%d%h")+".md"):
        self.filename = filename
        os.makedirs(logDir, exist_ok=True)
        self.logdir = logDir
        self.items = []
    
    def clear(self):
        self.items = []
    
    def addplt(self,name=""):
        if('.' in name):
            savename = name
        else:
            savename = os.path.join("imgs",name+str(int(time.time()*1000)) + ".png")
        print("\n![{}]({})\n".format(name,savename))

        os.makedirs(os.path.dirname(os.path.join(self.logdir,savename)),exist_ok=True)
        plt.savefig(os.path.join(self.logdir, savename))
        self.items.append(Docfig(savename,name))
    
    def addparagraph(self,content):
        print(content)
        self.items.append(Docparagraph(content))

    def generate(self):
        savename = os.path.join(self.logdir,self.filename)
        print(savename)
        with open(savename,"w") as f:
            for i in self.items:
                f.write(i.write())

        