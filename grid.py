# -*- coding: utf-8 -*-

# Lib-Imports
import simplejson
import copy

# Django imports
from django.forms import Media
from django.forms.widgets import Widget
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from django.core.paginator import Paginator, InvalidPage, EmptyPage

# Grid-Imports
from columns import Column
from exceptions import *
from resource_handler import GridResourceHandler

# Project-Settings
from django.conf import settings as project_settings


class Grid(Widget):
    """
    Grid-Widget for Django, that displays a dataset with pagination, enables sorting and filtering data, multi-column layout and so forth
    """

    # the js/css that is neccessary to operate the grid
    def _media(self):
        return Media(css = {'all':(self.resources.css("grid.css"), )},
                    js = (self.resources.js("grid.js"), ))
    media = property(_media)
    
    
    # Settings with a reasonable default
    __default_settings = {
        'grid_init_template' : 'grid_widget/grid_init.html',
        'grid_view_template' : 'grid_widget/grid_view.html',
        'column_head_template' : 'grid_widget/column_header.html',
        'column_content_template' : 'grid_widget/column_content.html',
        'width': 800,
        'entries_per_page': 20,
        'error_handler': "",
        'show_controls': True,
        
        # Settings which MUST be defined in the subclass
        'grid_id': None,
        'url': None,
    }
    
    def __init_settings(self, settings):
        """
        This will initialize the settings for this grid. This method will first read the defaults defined above,
        then parse all defined settings in the subclass. Afterwards it will adapt the settings given to the function.
        The resulting dictionary will be checked, if all required settings, as defined above, are present. If not
        a GridConfigurationException will be Thrown.
        @param settings The settings-dict given to init/view-function
        @throws GridConfigurationException If a required config is missing.
        """
        
        # set the defaults
        self.__settings = copy.deepcopy(self.__default_settings)
        
        # get the ones defined in the subclass
        for k, v in self.__default_settings.items():
            if k in dir(self):
                self.__settings[k] = getattr(self, k)
        
        # Update with the settings given to this function
        self.__settings.update(settings or {})
        
        
        # Check all required settings are given and != None
        for k, v in self.__default_settings.items():
            if self.__settings[k] == None:
                raise GridConfigurationException("Missing setting %s" % k)
            
        
    def __initialize_columns(self, request):
        """ This will read the column-infos from the grid-subclass and 
        call the initialize-method on all of them """
        self.__columns = []
        for attribute_name in dir(self):
            possible_column = getattr(self, attribute_name)
            
            # Check if the possible_column is really a column and if so, initialize it
            if isinstance(possible_column, Column):
                possible_column.initialize(request, attribute_name, self.__grid_id, self.__settings)
                self.__columns.append(c)
                
        # Sort all columns by their assigned number
        self.__columns = sorted(self.__columns, key=lambda c: c.get_nr())
        
        

    def __init__(self, request, init=True, settings=None):
        """
        Initialize a new grid. The constructor should never be called directly. Instead the methods init and view
        should be used, which capsulate the neccessary parameters and functionality for creating a the grid in the 
        requested mode
        @param request The django-Request-Object
        @param init Is the grid rendered or is the dataview rendered?
        @param settings Settings-Dictionary which is used to for getting some static vars like templates etc.
        """
        super(Widget, self).__init__()
        
        self.resources = GridResourceHandler(project_settings.STATIC_URL)

        # Read passed options
        self.__init = init
        self.__request = request
        
        # parse settings
        self.__grid_id = self.grid_id
        self.__init_settings(settings)
        
        # Initialise the columns
        self.__initialize_columns(self.__request)

    def get_id(self):
        """ Return the id of this grid """
        return self.__grid_id


    def render(self):
        """ This will start the rendering-process. If the grid is in init-mode, render_init will be called, otherwise render_content """
        return self.__render_init() if self.__init else self.__render_view()
    
    
    def get_request_parameters(self, request):
        """ This will load the request-parameters from the request and try to 
        convert them to json """
         # Load the params in the request
        if 'debug' in request.GET:
            state = request.GET['grid_data']
        else:
            state = request.POST.get('grid_data', '{}')
        parameter = simplejson.loads(state, "utf8")
        
        # Convert the keys to strings, because unicodes are not valid here!
        #unicode_fixed = dict([(str(k), v) for k, v in parameter.items()])
        return parameter
    
    # ============================================================================================
    # Init - Methods for creating the init-part of the grid

    @classmethod
    def init(cls, request, settings=None):
        """
        Render the initial part of the grid. This will return the html-code with javascript that will handle the rest 
        of the initialisation.
        @param request The request that issued the grid
        @param settings Optional dictionary with more settings. If given the settings will add/override the default ones
        """
        grid = cls(request=request, init=True, settings=settings)
        grid.__preset_filter = []
        grid.__extra_callback_params = {}
        grid.__extra_css_classes = []
        return grid
    
    
    def add_css_class(self, css_class):
        """ Add an additional class that should be appended to the grids div """
        self.__extra_css_classes.append(css_class)
    
    
    def preset_filter(self, column, value, mode="="):
        """
        preset a filter that should filter the data right from the beginning. 
        @param column The id of a column in the Grid. The column must be filterable
        @param value The value to filter with
        @param mode The mode to use while filtering
        """
        self.__preset_filter.append({"column": column, "mode": mode, "values": [value]})


    def add_callback_param(self, key, value):
        """ Add additional parameters that should be supplied to the grid-view-function
        @param key The key of the pair
        @param value The value of the pair
        """
        self.__extra_callback_params[key] = value
        

    def __render_init(self):
        """ This will create the init-html/js code of the grid. The code will be returned as safe-marked string """
        
        # resolve the url (Extract it because self.url() wont work and passes self to the lambda-function)
        url = self.__settings['url']
        url = url() if callable(url) else url
        
        context = {
            'id' : self.get_id(),
            'css_classes': self.__extra_css_classes,
            'url' : url,
            'preset_filter': mark_safe(simplejson.dumps(self.__preset_filter)),
            'error_handler': self.__settings['error_handler'],
            'extra_callback_params': mark_safe(simplejson.dumps(self.__extra_callback_params)),
        }
        
        return mark_safe(render_to_string(self.__settings['grid_init_template'], context, RequestContext(self.__request)))
        

    # ============================================================================================
    # View - Methods for rendering the datapart
        
    @classmethod
    def view(cls, request, queryset, settings=None):
        """
        This will prepare the grid for rendering in view-mode.
        @param request The request-object that issued the render
        @param queryset The queryset used to fetch the data. This will be manipulated by the grid
        @param settings Settings-dict that could override defaults
        @return Grid The newly created grid with the adjustments
        """
        grid = cls(request, init=False, settings=settings)
        parameters = grid.get_request_parameters(request)
        grid.prepare(queryset, parameters, for_viewing=True)
        return grid
    
    
    def prepare(self, queryset, parameters, for_viewing=True):
        """ Prepare the grid, columns and queryset for rendering. This will read the parameters and
        apply them to this grid. also each information for each column will be extracted and passed on
        @param queryset The queryset to operate on
        @param parameters Dict with all infos to prepare
        @param for_viewing If False, some steps are skipped (Such as sorting or paging, which only are relevant when viewing the data)
        """
        
        
        # Extract the page
        if for_viewing:
            self.__page = parameters.get('page', 1)
            paginator = Paginator(queryset.all(), self.__settings['entries_per_page'])
            try:
                queryset = paginator.page(self.__page)
            except InvalidPage, EmptyPage:
                self.__page = 1
                queryset = paginator.page(1)


    def __render_view(self):
        """
        This is called by the render-method and should create the html that represents the dataview of the grid
        @return String safe-marked string that contains the html-code
        """
        
        # Prepare the width of the Columns
        #self.__calculate_width()


        # Render the header
        rendered_heads = [c.render_head() for c in self.__columns]
        
        # render the columns
        rendered_rows = []
        for row in self.__model:
            data = []
            for column in self.__columns:
                if column.is_visible():
                    data.append(column.render_content(self.__request, row))
            rendered_rows.append({'id': row.get_value('pk'), 'data':data})
        
        # Get the paginator infos
        page = self.__model.get_page()
        
        # Get invisible filters and add neccessary info
        invisible_filter = []
        for c in self.__columns:
            if not c.is_visible() and c.show_filter_if_hidden():
                invisible_filter.extend(self.__model.get_filter(c.get_id()))
        for f in invisible_filter:            
            f['mode'] = Column.Filter.get_mode_description(f['mode'])
        
                
        # Prepare the context
        context = {
            'id': self.get_id(),
            'head': rendered_heads,
            'rows': rendered_rows,
            'current_page': page['current'],
            'has_next_page': page['next'],
            'has_prev_page': page['prev'],
            'num_pages': page['count'],
            'extra_filter': invisible_filter,
            'show_controls': self.__settings['show_controls'],
        }
        return render_to_response(self.__settings['grid_view_template'], context, context_instance=RequestContext(self.__request))
        

    # ============================================================================================
    # Data - Methods for generating a gridmodel for aggregating

    @classmethod
    def data(cls, request, model, settings=None):
        """
        This will prepare a model and supply it with the same options the 
        grid used to prepare itself. The returned model can be used while aggregating
        This will prepare the grid for rendering in view-mode.
        @param request The request-object that issued the render
        @param model The model that should be used to prepare the data
        @param settings Additional Settings to pass to the grid
        @return gridModel Prepared Grid-model
        """
        # Check the model is in aggregation-mode
        if not model.is_aggregated():
            raise Exception(u"The provided model is supposed to be aggregated!")
        
        # Create the grid
        grid = cls(request, init=False, state_handler=None, text_handler=None, settings=settings)
        grid._set_model(model)       

        # prepare the model (Sorting, filter, ...)
        state = request.POST.get('grid_data', '{}')
        parameter = simplejson.loads(state, "utf8")
        # Convert the keys to strings, because unicodes are not valid here!
        unicode_fixed = dict([(str(k), v) for k, v in parameter.items()])
        model.prepare(**unicode_fixed)

        return model
    
