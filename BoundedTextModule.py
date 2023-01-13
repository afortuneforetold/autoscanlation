class BoundedTextModule:
    
    def __init__(self, description = "", bound = []):
        self.description = description
        self.bound = bound
        self.sub_modules = []
        
    def get_description(self, divider = ""):
        if self.description: 
            return self.description
        return divider.join([x.get_description() for x in self.sub_modules])
    
    def add_module(self, module, idx=-1):
        if idx < 0:
            self.sub_modules.append(module)
        else:
            self.sub_modules.insert(module, idx)
        self.update_bound(module)
            
    def merge_module(self, module, mode=0):
        if mode == 0:
            if self.description:
                self.description += module.get_description()
            else:
                self.sub_modules += module.sub_modules
        else:
            if self.description:
                self.description =  module.get_description() + self.description
            else:
                self.sub_modules = module.sub_modules + self.sub_modules
        self.update_bound(module)
                
                
    def update_bound(self, module):
        if not self.bound:
            self.bound = module.bound
        else:
            self.bound = [
                min(self.bound[0], module.bound[0]),
                min(self.bound[1], module.bound[1]),
                max(self.bound[2], module.bound[2]),
                max(self.bound[3], module.bound[3]),
            ]
            
    def depth(self):
        if self.description or not self.sub_modules:
            return 0
        return max([x.depth() for x in self.sub_modules]) + 1
            
    def __str__(self):
        return "{} {} depth: {}".format(self.get_description(), self.bound, self.depth())