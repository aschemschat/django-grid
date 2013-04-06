# -*- coding: utf-8 -*-

# Django Imports
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.template.context import RequestContext

#from columns_filter import Filter
#from columns_width import Width
#from model_base import InvalidFilterException

class Width(object):
    NORMAL = 1
    ICON = 2

from datetime import date
import re

# Grid Imports
from resource_handler import GridResourceHandler

# Project-settings
from django.conf import settings as project_settings


class Column(object):
    """
    This represents the basic renderer for columns. It contains a render_head- and render_content-method
    that will render the data and return the html-code for this column
    """
    
    # Set as object of Column, so the Width is accessible as a Property of Column (For writing Column.Width.SMALL in the definition of the grid)
    Width = Width
    #Filter = Filter
        
    # ID-Counter for each column
    nr_counter = 0

    def __init__(self, label=None, db_field=None, obj_field=None, visible=True, sortable=True, nullable=False, filterable=False, show_filter_if_hidden=True, styles=None, classes=None, widthtype=Width.NORMAL):
        """
        Init a new column-instance
        @param label 
            The label that is used to display the columnheader. If the label is callable the function will be 
            called and the return used as header, otherwise the label will be used as is.
            If the label is None the id of the Column will be used
        @param db_field
            The field that contains the data of this field. `.` can seperate variable-names, if the data lies within a deeper
            object. If db_field is None, the id will be used as default
        @param obj_field db_field just for the object-access. If not given db_field will be used
        @param visible Will this column be shown in the grid? 
        @param sortable Should the Column be sortable?
        @param nullable May this column be null?
        @param show_filter_if_hidden If the column is not visible, should the filter be displayed beneath the grid?
        @param styles This may be a dictionary with additional styles the column should have
        @param classes Additional CSS-Classes for the column
        @param widthtype Assign a width to the column. 
        """
        # Assign a unique nr
        self.__nr = Column.nr_counter
        Column.nr_counter += 1
        
        # Get a resource-handler
        self.resouces = GridResourceHandler(project_settings.STATIC_URL)
        
        # Store options
        self.__label = label
        self.__db_field = db_field
        self.__obj_field = obj_field
        self.__sortable = sortable
        self.__visible = visible
        self.__nullable = nullable
        self.__filterable = filterable
        self.__show_filter_if_hidden = show_filter_if_hidden
        self.__styles = styles if styles != None else {}
        self.__classes = classes if classes != None else []
        self.__widthtype = widthtype

        # placeholder        
        self._filter = None
        self.__column_id = None
        self.__settings = None
        self.__grid_id = None
        
        
    def initialize(self, request, column_id, grid_id, settings):
        """
        This will called once the grid is initialized. This method will init some values, that couldnt be initialized
        before the id is fixed, which can only be obtained once the grid initialized all columns
        @param reqeust The current request
        @param column_id  The id the grid assigned for this column
        @param grid_id The id of the grid
        @param settings Dictionary containing some constant setup-variables (like template-pathes, image-basefolder, ....)
        """
        self.__request = request
        self.__column_id = column_id
        self.__grid_id = grid_id
        self.__settings = settings
        self.__label = column_id if self.__label == None else self.__label
        self.__db_field = column_id if self.__db_field == None else self.__db_field
        self.__obj_field = self.__obj_field if self.__obj_field != None else self.__db_field
        
        # make filter nullable, if column is nullable
        # TODO: Filter
        #if self.__nullable:
            #self._filter.make_nullable()
            
    def prepare_for_render(self, queryset, data):
        """ This will prepare the queryset with the data given and adapt this column to 
        the given data.
        @param queryset The query-set the grid is based on
        @param data The data given for this column (Like filtering, sorting, ...)
        """
        pass
    
    
    def render_head(self, request):
        """
        This will render the head-cell of the columnwidget. 
        @param The request that is issued the render
        @param model The model that contains the data. This neccessary to render the sorting and filters
        @return Safe-marked html-string containing the code for the head
        """
        
        # prepare the sorting
        if self.__sortable:
            sorted_ascending = model.get_sorting(self.get_id())
            sorted = {
                'current': {None: 0, True: 1, False: -1}.get(sorted_ascending),
                'next': {None: 1, True: -1, False: 1}.get(sorted_ascending)
            }
        else:
            sorted = None

        # Prepare the filter
        if self._filter:
            filter_active = model.get_filter(self.get_id()) #Format: {nr, id, value, mode, success}
            filter_widget = self._filter.render()
            
            for f in filter_active:
                f['mode'] = mark_safe(Filter.get_mode_description(f['mode']))
        else:
            filter_active = None
            filter_widget = None
        
        
        # Start the rendering   
        context = {
            # Ids
            'grid_id' : self.__grid_id,
            'column_id' : self.get_id(),
            
            # Basic things
            'label' : self.__label() if callable(self.__label) else self.__label,
            'styles': self.__styles,
            'classes': self.__classes,
            'visible': self.__visible,
            
            # Extras (Sorting, filter, ...)
            'sorted' : sorted,
            'filter': filter_active,
            'filterwidget': filter_widget,
            'show_controls': self.__settings['show_controls'],
        }
        
        return mark_safe(render_to_string(self.__settings['column_head_template'], context, RequestContext(request)))
    
    def render_content(self, request, row):
        """
        This will render the content-coll of the column for a specified object/data-set
        @param row The row that was supplied by the model
        @return Safe-marked html-string containing the code for the cell
        """        
        context = {
            'content' : mark_safe(self._render_data(row))
        }

        return mark_safe(render_to_string(self.__settings['column_content_template'], context, RequestContext(request)))
            
   
    def _render_data(self, data):
        """
        This function must be overwritten by each child and should return a string containing the html-code to render as 
        response
        @param data The data-row from which to fetch the data
        @param value The object to display
        """
        raise NotImplementedError()
    

        


# ==========================================================================================================
# ==========================================================================================================
#    Special instances of the Column which must be used instead of the parent-column

class TextColumn(Column):  
    """ Column for displaying simple text-values """
    
    
    def __init__(self, *args, **kw):
        super(TextColumn, self).__init__(*args, **kw)        
        #self._filter = TextColumn.Filter()
        
    def _render_data(self, row):
        """ Render the content of the textColumn """
        value = row.get_value(self.get_id())
        return value if value != None else ""
    
   