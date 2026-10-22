function estaciones = cargar_estaciones(sc, tipo)
%CARGAR_ESTACIONES Agrega al escenario las estaciones de data/estaciones.csv.
%   estaciones = cargar_estaciones(sc) agrega todas las estaciones.
%   estaciones = cargar_estaciones(sc, "downlink") agrega solo ese tipo.
%
%   Así los scripts de MATLAB y la herramienta de Python comparten
%   exactamente las mismas coordenadas.

    if nargin < 2
        tipo = "";
    end

    ruta = fullfile(fileparts(mfilename("fullpath")), "..", "data", "estaciones.csv");
    datos = readtable(ruta, "TextType", "string", "Encoding", "UTF-8");
    if tipo ~= ""
        datos = datos(datos.tipo == tipo, :);
    end

    estaciones = cell(height(datos), 1);
    for k = 1:height(datos)
        estaciones{k} = groundStation(sc, ...
            "Name", datos.nombre(k), ...
            "Latitude", datos.latitud(k), ...
            "Longitude", datos.longitud(k), ...
            "Altitude", datos.altitud_m(k));
    end
end
