'use strict';
angular.module("olmap", []).directive("olMap", ["$http", function($http) {

var map = null;

  function add_layer(wfs_url) {
      var geojson_format = new OpenLayers.Format.GeoJSON();
      var layer_style = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
      layer_style.fillOpacity = 0.8;
      layer_style.graphicOpacity = 1;

      var renderer = OpenLayers.Util.getParameters(window.location.href).renderer;
      renderer = (renderer) ? [renderer] : OpenLayers.Layer.Vector.prototype.renderers;
      var bbox = map.getExtent().toBBOX();
      var params = {
        bbox: bbox,
        maxfeatures: 100000
      };

      $http.get(wfs_url + "/all.json", {"params": params}).success(function(results) {
          var feature_collection = results;
          var vlayer = new OpenLayers.Layer.Vector("test", {
              style : layer_style,
              renderers : renderer
          });

          map.addLayer(vlayer);
          vlayer.addFeatures(geojson_format.read(feature_collection));
      });
  }

  function init_map(div_id, lon, lat, zoom) {
      map = new OpenLayers.Map(div_id, {
          div : div_id,
          projection : new OpenLayers.Projection("EPSG:900913")
      });

      var layer = new OpenLayers.Layer.OSM();
      map.addLayer(layer);
      map.addControl(new OpenLayers.Control.LayerSwitcher());
      map.setCenter((new OpenLayers.LonLat(lon, lat)).transform(new OpenLayers.Projection("EPSG:4326"), map.getProjectionObject()), zoom);
  }

  return {
      scope : {
          center : '=',
          zoom : '=',
          wfsLayers : '='
      },

      restrict : 'EA',

      link : function(scope, elem, attrs) {
          var elem_id = attrs["id"];
          if (elem_id) {
              init_map(elem_id, scope.center[1], scope.center[0], scope.zoom);
          } else {
              console.error("offMap directive requires id to be specified");
          }
          scope.$watch("wfsLayers", function(arr) {
              angular.forEach(arr, function(val, idx) {
                  console.log("loading " + val);
                  add_layer(val);
              });
          });
      }
  };
}]);
