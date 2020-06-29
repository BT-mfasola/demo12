(function($) {
    $.fn.ksResizableColumns = function(option) {
      var isColResizing = false;
      var resizingPosX = 0;
      var _table = $(this);
      var _thead = $(this).find('thead');
      var is_resize_dirty = false;
      var $col_target = false;

      var update = option.update || function(){};

        const _onClickResize = function(ev){
            ev.stopPropagation();
            ev.preventDefault();
        };

        const _onStartResize = function(e){
            // Class Used to identify changes : 'ks_resize', 'ks_resizer', 'ks_resizing'

            if (e.which !== 1) {
                return;
            }
            e.preventDefault();
            e.stopPropagation();

            $col_target = $(e.target);
            _thead.find('th').removeClass('ks_resizing');
            $(_thead).find('tr:first-child th:nth-child(' + ($(this).closest('th').index() + 1) + ') .ks_resizer').closest('th').addClass('ks_resizing');
            isColResizing = true;
            resizingPosX = e.pageX;

            const table = _table[0];
            const resizeStoppingEvents = [
                'keydown',
                'mousedown',
                'mouseup',
            ];

            // Apply classes to table and selected column
            table.classList.add('ks_resize');

            // Mousemove event : resize header
            const resizeHeader = e => {
                e.preventDefault();
                e.stopPropagation();

                if (isColResizing) {
                  is_resize_dirty = true;
                  var _resizing = _thead.find('th.ks_resizing .ks_resizer');
                  if (_resizing.length) {
                    var _pageX = e.pageX || 0;
                    var _widthDiff = _pageX - resizingPosX;
                    var _setWidth = _resizing.closest('th').innerWidth() + _widthDiff;

                     if($.find("th.o_many2many_tags_cell").length){
                        var ks_many2many_tag_width = $($.find("th.o_many2many_tags_cell")).innerWidth();
                        $($.find(".o_field_widget.o_field_many2manytags .badge .o_badge_text")).css("max-width",String(ks_many2many_tag_width)+"px");
                        $($.find(".o_field_widget.o_field_many2manytags")).css("max-width",String(ks_many2many_tag_width)+"px");
                    }

                    if (resizingPosX != 0 && _widthDiff != 0 && _setWidth > 0 ) {
                      _table.innerWidth(_table.innerWidth()+_widthDiff);
                      resizingPosX = e.pageX;
                      _thead.innerWidth(_table.innerWidth()+_widthDiff);
                      _resizing.closest('th').innerWidth(_setWidth);
                    }
                  }
                }
            };
            window.addEventListener('mousemove', resizeHeader);

            const stopResize = ev => {
                if (ev.type === 'mousedown' && ev.which === 1) {
                    return;
                }
                ev.preventDefault();
                ev.stopPropagation();
                // We need a small timeout to not trigger a click on column header
                clearTimeout(this.resizeTimeout);
                this.resizeTimeout = setTimeout(() => {
                    if (is_resize_dirty && $col_target) update($col_target);
                    _thead.find('th').removeClass('ks_resizing');
                    is_resize_dirty = false;
                    isColResizing = false;
                }, 100);
                window.removeEventListener('mousemove', resizeHeader);
                table.classList.remove('ks_resize');
                resizeStoppingEvents.forEach(stoppingEvent => {
                    window.removeEventListener(stoppingEvent, stopResize);
                });


                document.activeElement.blur();
            };

            resizeStoppingEvents.forEach(stoppingEvent => {
                window.addEventListener(stoppingEvent, stopResize);
            });
        };

      _thead.find(".bg-primary th").each(function() {
        $(this).css('position', 'relative');
        if (!($(this).text() === "S.No" || $(this).hasClass("o_list_record_selector"))){

            const resizeHandle = document.createElement('div');
            resizeHandle.classList = 'ks_resizer';
            $(resizeHandle).css({
                'position': 'absolute',
                'top': '0px',
                'right': '-3px',
                'bottom': '0px',
                'width': '10px',
                'z-index': '999',
                'background': 'transparent',
                'cursor': 'col-resize'
            })

            resizeHandle.onclick = _onClickResize.bind(this);
            resizeHandle.onmousedown = _onStartResize.bind(this);
            $(this).append(resizeHandle);
        }
      })

    };
  }
(jQuery));
