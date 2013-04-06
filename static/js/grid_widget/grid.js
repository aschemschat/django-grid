// ==========================================
// This little part is responsible for managing 
// the grids on the page. 

var grids = {}
function getGrid(id) {
    return grids[id];
}
function addGrid(options) {
    if(grids[options.id] == null)
        grids[options.id] = new GridJS(options);
}

// ==========================================
//      Functions for filter-options

function GridFilter(grid, column) {
    
    /** Init the new filter */
    this.init = function(grid, column) {
        // initialise variables
        this.grid = grid;
        this.column = column;
        this.$_show = $("#" + grid + "_" + column + "_filter_show");
        this.$_form = $("#" + grid + "_" + column + "_filter_form");
        this.$_regex = this.$_form.children('.grid_filter_form_regex');
        this.$_mode = this.$_form.children('.grid_filter_form_mode');        
        this.$_inputs = this.$_form.children('.grid_filter_form_input');
        this.$_addbutton = this.$_form.find('.grid_filter_form_add > img');
        this.regex = (this.$_regex.val() != "") ? new RegExp(this.$_regex.val(), 'i') : null;
        this.enabled = true;
        
        // register events
        var filter = this;
        
        // show the filter-menu when clicking on img (first check if visible, otherwise it will just reopen)
        this.$_show.click(function() {
            if(filter.$_form.is(':visible')) {
                filter.hide_all_forms();
            }
            else {
                filter.hide_all_forms();
                filter.show_form();
            }
            return false;
        });
            
        // add a new filter when clicking the add-button
        this.$_form.find('.grid_filter_form_add').click(function() {
            if(filter.enabled) {
                filter.add_filter();
                filter.hide_all_forms(); 
            }
            return false;
        });
            
        // also add the new filter if enter was pressed or hide window if esc
        this.$_form.find('.grid_filter_form_input').keypress(function(event) {
            if(event.keyCode == 13) {
                if(filter.enabled) {
                    filter.add_filter();
                    filter.hide_all_forms();
                }
            }
            else if(event.keyCode == 27) {
                filter.hide_all_forms();
            }
        });
            
        // add the cancel element
        this.$_form.find('.grid_filter_form_cancel').click(function() {
            filter.hide_all_forms();
        });
   
        // prevent clicks withing the div from bubbling
        this.$_form.click(function() {
            return false;
        });

        // register the regex-validation, if a regex is present
        this.$_form.children('.grid_filter_form_input').keyup(function() {
            filter.check_requirements();
        });
        
        // register any change in the mode and check requirements
        this.$_form.children('.grid_filter_form_mode').change(function() {
            filter.check_requirements();
        });
    }
    
    /** Hide all filterforms and reset them */
    this.hide_all_forms = function() {
        this.$_form.hide();
        this.$_inputs.removeClass('grid_filter_form_input_invalid').val('');
    }
    
    /** Return the the needed amount of inputs for the currently selected mode */
    this.get_inputs_for_current_mode = function() {
        return parseInt(this.$_mode.is('input') ? this.$_mode.attr('data-inputs') : this.$_mode.children('option:selected').attr('data-inputs'));
    }
    

    /** Add a new filter to the grid */
    this.add_filter = function() {
        var values = Array();
        for(var i=0; i < this.get_inputs_for_current_mode(); ++i)
            values.push(this.$_inputs.eq(i).val());
        getGrid(this.grid).addFilter(this.column, values, this.$_mode.val());
    }
    
    /**
     * This will show the filterform and set the focus to the input. If a regex is defined
     * for this form it will be checked here initialy
     */
    this.show_form = function() {
        // Disable Filter-Button if Filter is not valid yet (->a regex is not matched)
        this.check_requirements();  
    
        // now open the one we want
        this.$_form 
            .show()
            .children('.grid_filter_form_input')
            .focus();
    }

    /**
     * This will check the requiremtnts for this filterform. 
     * If a regex is defined, it will be checked (add-button disabled, background red)
     * Further checks may be added in the future 
     * @param $_form The form too check 
     */
    this.check_requirements = function() {
        var valid = true;
        
        // iterate through inputs
        for(var i=0; i < this.get_inputs_for_current_mode(); ++i) {
            var $_input = this.$_inputs.eq(0);
            // check regex and input not empty
            if($_input.val() == "" || (this.regex && !this.regex.test($_input.val()))) {
                $_input.addClass('grid_filter_form_input_invalid');                
                valid = false;
            }
            else {
                $_input.removeClass('grid_filter_form_input_invalid');
            }
        }
        
        // if one is not valid, deactivate button
        if(valid) {
            this.$_addbutton.attr('src', static_url+'/img/grid/add_filter.png');
            this.enabled = true;
        }
        else {
            this.$_addbutton.attr('src', static_url+'/img/grid/add_filter_deactivated.png');
            this.enabled = false;
        }
     
        // show the amount of inputs that is needed
        this.$_inputs.hide();
        for(var i=0; i < this.get_inputs_for_current_mode(); i++) {
            this.$_inputs.eq(i).show();
        }
    }
    
    
    this.init(grid, column);
}


// ==========================================

/**
 * Main-Class for the grid.
 * 
 * Events: grid:reloaded If the grid was reloaded (TODO)
 * 
 */
var Grid = (function() {
    
    /** Initialize a new grid. Options contains the settings */
    function Grid(options) {
        console.assert(options.id && options.url);
        
        // read options
        this.id = options.id;
        this.url = options.url;
        this.error_handler = options.error_handler || null;
        
        // find elements
        this.$grid = $("#grid_" + this.id);
        console.assert(this.$grid.length == 1);
        
        
        // extract extra callback-params
        this.extra_callback_params = options.extra_callback_params || {};
        
        this.debug("initialized");
        
        // initial reloading
        this.reload();
    }

    /** Print a debug-message to the console */
    Grid.prototype.debug = function(msg) {
        console.log("Grid `" + this.id + "`: " + msg);
    }
    
    /** 
     * This function is called, once a reload of the page is issued 
     */
    Grid.prototype.reload = function() {
        this.debug("starting reload...");
        
        params = {}
        
        // load hashurl-data
        params['page'] = 1;
        
        // extra-callback-params
        $.each(this.extra_callback_params, function(key, value) {
            params[key] = value;
        });
        
        this.post_request(params);
    }
    
    /**
     * Make the actuall request to the webserver and replace the html with the result 
     */
    Grid.prototype.post_request = function(params) {
        var self = this;
        
        // The callback-Function 
        var callback = function(responseText, textStatus, XMLHttpRequest) {
            self.debug("received Answer");
            self.$grid.removeClass("grid_loading");
            
            if(textStatus == "success") {
                self.$grid.trigger("grid:reloaded", [self, params]);
            }
            else {
                self.error_handler(self, "An error occured while Loading!", params);
            }
        };
        
        this.$grid.addClass("grid_loading");   
        this.$grid.load(this.url, {'grid_data': params}, callback);
    }
    
    
    return Grid;
})();


function GridJS(options)
{
    
    /**
    * This will initialise a new grid and make all neccessary changes
    */
    this.init = function(options)
    {
        this.id = options['id'];
        this.url = options['url'];
        this.extra_view_params = options['extra_view_params'];
        this.error_handler = function(msg) {
            hsf.messages.error(msg);
        };         
        
        // define values
        this.page = null;
        this.sorting = {};
        this.filter = {};
        this.filterNr = 0;
        this.updateFunctions = new Array();
        
        // load initial values from saved state
        if(options.initial_state) {
            if(options.initial_state.page) {
                this.page = options.initial_state.page;
            }
            if(options.initial_state.sorting) {
                this.sorting = options.initial_state.sorting;
            }
            if(options.initial_state.filter) {
                for(var i in options.initial_state.filter) {
                    var f = options.initial_state.filter[i];
                    this.filter[f.nr] = f;
                }
            }
        }
        
        // if there are extra filter specified delete the old ones and set the new ones
        if(options.extra_filter && options.extra_filter.length > 0) {
            this.clearFilter();
            for(var i in options.extra_filter) {
                var f = options.extra_filter[i];
                this.addFilter(f['column'], f['values'], f['mode'], false);
            }
        }
 
        // start first update
        this.update();
    }
    
    /**
     * Fuegt eine JS-FUnktion hinzu, die aufgerufen werden soll, wenn das Grid geupdatet wird.
     * Die funktion kriegt ein Objekt, dass die gleichen Parameter wie das original-Grid enthaelt
     */
    this.addUpdateFunction = function(func) {
        this.updateFunctions.push(func);
    }
 
    
    /**
    * This function will get the grid to load the specified page. The page is definied
    * by the current active rows per page. For example page 2 with a limit of 10 will display
    * the entries 10-19.
    * @param number The page to go to. 
    */
    this.toPage = function(number)
    {
        this.page = number;
        this.update();
    }
    
    /**
    * This will change the current sorting order.
    * @param column The column that should be sorted
    * @param direction May be 'asc' oder 'desc'
    */
    this.sort = function(column, direction)
    {
        this.sorting = {'column':column, 'direction':direction};
        this.update(); 
    }
    
    /**
    * This method will add a new filter to the specified column. 
    */
    this.addFilter = function(column, value, mode, update)
    {
        if(value == "")
            return;
        
        // iterate over the filter-array and find the first free number to insert in
        inserted = false;
        while(!inserted) {
            if(!this.filter[this.filterNr]) {
                this.filter[this.filterNr] = {'nr':this.filterNr, 'id':column, 'values':value, 'mode': mode};
                inserted = true
            }
            this.filterNr++;
        }
        
        if(update != false)
        	this.update();
    }

    /**
    * This will deleted a specified filter from the list
    */
    this.removeFilter = function(id)
    {
        delete(this.filter[id]);
        this.update();
    }
    
    /**
     * This will reset all current filter. This function will not update
     */
    this.clearFilter = function()
    {
        this.filter = {}
        this.filterNr = 0;
    }
    
    /**
     * This will reset the entire grid-status to the default
     */
    this.reset = function() {
    	this.page = null;
        this.sorting = {};
        this.filter = {};
        this.filterNr = 0;
        this.update();
    }
    
    /**
    * This will load a new set of data via the Ajax-Callback
    */
    this.update = function(full_update)
    {
        if(full_update == null)
            full_update = true;
        
        var $_grid = $('#' + this.id);
        $('#'+this.id).addClass('grid_loading');
        
        // building the param-object from the internal states
        params = {};
        if(this.page != null)
            params['page'] = this.page;
            
        // ... sorting
        if(this.sorting != null)
            params['sorting'] = this.sorting;

        // ... filter
        params['filter'] = Array();
        for(f in this.filter)
            params['filter'].push(this.filter[f]);
           
        // ... initial load?
        // params['initial_load'] = this.initial_load;

        // ... callbackdata
        for(key in this.extra_view_params)
            params[key] = this.extra_view_params[key];
            
        // Post the request and process the answer
        if(full_update)
        	this.update_grid($.toJSON(params));
        else
        	this.update_hooks($.toJSON(params));        		
    }
    
    /**
     * This will update the grid
     */
    this.update_grid = function(params) {
    	var $_grid = $('#' + this.id);
    	var instance = this;
    	$_grid.load(this.url, {'grid_data': params}, function(responseText, textStatus, XMLHttpRequest) 
    	{
    		$_grid.removeClass('grid_loading');
               
            // on success add the text
            if(textStatus == "success") {
            	instance.update_hooks(params);
            }
            else {
                if(instance.error_handler)
                    instance.error_handler("Ein unerwarteter Fehler ist beim laden der Tabelle aufgetreten. Bitte unten klicken um die Ansicht zur&uuml;ck zu setzen");
                $_grid
                    .html("")
                    .append("<img class='grid_error' src='" + static_url+"/img/info/grid_error.png' />")
                    .click(function() {
                        instance.reset();
                    });
            }            
    	});
    }
    
    /** 
     * This will call all update-functions
     */
    this.update_hooks = function(params) {
    	// Alle updateFunctions aufrufen
        for(func in this.updateFunctions)
                this.updateFunctions[func](params);
    }
    
    
    // Initialise the grid (Call the CTor so to say)
    this.init(options);    
}