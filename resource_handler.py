class GridResourceHandler(object):
    """
    This class is used to fetch the urls to display resources, like images, css and js
    It is initialized with a static_path, which is the base-url to the static files.
    
    """
    
    def __init__(self, static_path=None):
        """ 
        Initialize the mixin. The `static_path` is the baselocation to all
        images 
        """
        self.__static_path = static_path
        
    
    def __resource(self, resource_type, name):
        """ This will return the absolute url to the resource. The resource_type
        may be css, js, img and the name specifies the name to use """
        return u"%s/%s/grid_widget/%s" % (self.__static_path, resource_type, name)
        
    def css(self, name):
        return self.__resource("css", name)
    
    def js(self, name):
        return self.__resource("js", name)
    
    def icon(self, name, deactivated=False):
        img_name = u"%s%s" % (name, "" if not deactivated else "_deactivated")
        return self.__resource("img", name)