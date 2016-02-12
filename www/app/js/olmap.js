'use strict';
angular.module("olmap", []).directive("olMap", ["$http", "$q",
function($http, $q) {
    
    var map = null, baseUrl = "http://127.0.0.1:5000/api/";
    
    function show_rastertiles(rastertiles) {
        var gj = {
              'type': 'FeatureCollection',
              'crs': {
                'type': 'name',
                'properties': {
                  'name': 'EPSG:900913'
                }
              }
        };
        
        var features = [];
        for (var i=0; i<rastertiles.length; i++) {
            var id = rastertiles[i]["id"];
            var rast = rastertiles[i]["rast"];
            
            if (rast.hasOwnProperty("extent")) {
                features.push({
                    'type': 'Feature',
                    'geometry': rast.extent
                });    
            }
            
            if (rast.hasOwnProperty("length")) {
                for (var j=0; j<rast.length; j++) {
                    var cell = rast[j][0]; //coordinates, type
                    var val = rast[j][1];
                    features.push({
                        'type': 'Feature',
                        'geometry': cell,
                    });
                }
            }
        }
        
        gj["features"] = features;
        console.log(gj);
        
        var layer_style = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
        layer_style.fillOpacity = 0.8;
        layer_style.graphicOpacity = 1;

        var renderer = OpenLayers.Util.getParameters(window.location.href).renderer;
        renderer = (renderer) ? [renderer] : OpenLayers.Layer.Vector.prototype.renderers;
        
        var vlayer = new OpenLayers.Layer.Vector("test", {
            style : layer_style,
            renderers : renderer
        });
        map.addLayer(vlayer);
        
        var geojson_format = new OpenLayers.Format.GeoJSON();
        vlayer.addFeatures(geojson_format.read(gj)); 
    }

    function get_provider(provider_name) {
        var url = baseUrl + "provider";
        var def = $q.defer();
        $http({
            url: url,
            method: "GET",
            params: {
                "q": {
                    "filters": [{
                        "name":"name", 
                        "op": "==", 
                        "val": provider_name
                    }]
                }
            }
        }).success(function(results) {
            def.resolve(results.objects);
        });
        return def.promise;
    }
    
    function get_datagranules(provider) {
        var url = baseUrl + "datagranule";
        var def = $q.defer();
        $http({
            url: url,
            method: "GET",
            params: {
                "q": {
                    "filters": [{
                        "name":"provider_id", 
                        "op": "==", 
                        "val": provider.id
                    }]
                }
            }
        }).success(function(results) {
            def.resolve(results.objects);
        });
        return def.promise;
    }
    
    function get_rastertiles(datagranule) {
        var url = baseUrl + "rastertile/" + datagranule.id;
        var def = $q.defer();
        $http({
            url: url,
            method: "GET"
        }).success(function(results) {
            def.resolve(results.tiles);
        });
        return def.promise;
    }
    
    function init_map(div_id, lon, lat, zoom) {
        map = new OpenLayers.Map(div_id, {
            div : div_id,
            projection : new OpenLayers.Projection("EPSG:900913")
        });

        var layer = new OpenLayers.Layer.OSM();
        map.addLayer(layer);
        map.addControl(new OpenLayers.Control.LayerSwitcher());
        map.setCenter((new OpenLayers.LonLat(lon, lat)).transform(new OpenLayers.Projection("EPSG:4326"), 
            map.getProjectionObject()), zoom);
    }

    return {
        
        scope : {
            center : '=',
            zoom : '='
        },

        restrict : 'EA',

        link : function(scope, elem, attrs) {
            var elem_id = attrs["id"];
            if (elem_id) {
                init_map(elem_id, scope.center[1], scope.center[0], scope.zoom);
            } else {
                console.error("offMap directive requires id to be specified");
            }
            
            get_provider("GFS").then(function(providers) {
                get_datagranules(providers[0]).then(function(granules) {
                   get_rastertiles(granules[0]).then(function(rastertiles) {
                      var page = 1,
                          total_pages = rastertiles.total_pages;
                      show_rastertiles(rastertiles);
                   });
                });
            });
        }
    };

}]);
