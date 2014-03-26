$.screenshots = function(url_list,screenshot_div,background_div) {
  var current_image;
  var image_holder = screenshot_div.find( '.image-holder' );
  background_div.hide();
  var index=-1;
  
  var next_index = function() {
    var new_index = index + 1
    if (new_index>=url_list.length) {
      new_index = 0;
    }
    return new_index;
  }
  var load_next = function() {
    var img = $('<img />');
    img.attr( 'src', next_record().url );
    background_div.empty();
    background_div.append( img );
  };
  var as_record = function( maybe ) {
      if ($.type(maybe)==='string') {
          return { 'url':maybe };
      } else {
          return maybe;
      }
  };
  var current_record = function() {
    return as_record( url_list[index] );
  };
  var next_record = function() {
    return as_record( url_list[next_index()] );
  }
  
  load_next();
  
  var show_loaded = function(record) {
    var loaded = background_div.find( 'img' );
    if (loaded.length) {
        current_image = loaded;
        var target_width = screenshot_div.width();
        var target_height = screenshot_div.height();
        var target_ratio = target_height/target_width;
        var width, height, ratio;
        width = loaded[0].naturalWidth;
        height = loaded[0].naturalHeight;
        if ((! width) || (! height)) {
            return;
        }
        ratio = height/width;
        if (ratio > target_ratio) {
            // Image is narrower than target...
            loaded.css( {
                'height': target_height,
                'width': target_height / ratio
            });
        } else {
            loaded.css( {
                'height': target_width * ratio,
                'width': target_width
            });
        }
        image_holder.empty();
        loaded.hide();
        image_holder.append( loaded );
    }
    load_next();
    if (loaded.length) {
        loaded.show( 250, function() {
            var text = record.description || '';
            screenshot_div.find( '.description' ).text( text );
            
            var link = record.link;
            if (link) {
                screenshot_div.find( 'a' ).attr( 'href', link );
            } else {
                screenshot_div.find( 'a' ).removeAttr( 'href' );
            }
        } );
        loaded.click( next_image );
    }
  };
  
  var next_image = function() {
    index = next_index();
    var to_display = current_record();
    if (current_image && current_image.length) {
        current_image.hide( 250, function() {
            show_loaded(to_display);
        });
    } else {
        show_loaded(to_display);
    }
  }
  window.setInterval( next_image, 5000 );
  next_image();
};
