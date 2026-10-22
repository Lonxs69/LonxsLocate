% Create satellite communication scenario
sc = satelliteScenario;

% General parameters
simulationDuration = hours(24); % Simulation duration
sc.StopTime = datetime("now") + simulationDuration;

% --- GEO ORBIT ---
% GEO orbital parameters
semiMajorAxisGEO = 42164e3; % GEO semi-major axis (Earth radius + altitude)
eccentricityGEO = 0; % Circular orbit
inclinationGEO = 0; % Equatorial orbit
raanGEO = 0; % Right Ascension of the Ascending Node
argumentOfPeriapsisGEO = 0; % Argument of periapsis
trueAnomalyGEO = 0; % Initial true anomaly

% Create satellite in GEO
geoSat = satellite(sc, semiMajorAxisGEO, eccentricityGEO, ...
    inclinationGEO, raanGEO, argumentOfPeriapsisGEO, trueAnomalyGEO, ...
    "Name", "GEO Sat");

% --- LEO ORBIT ---
% LEO orbital parameters
semiMajorAxisLEO = 7000e3; % LEO semi-major axis (Earth radius + altitude)
eccentricityLEO = 0; % Circular orbit
inclinationLEO = 98; % Polar inclination
argumentOfPeriapsisLEO = 0; % Argument of periapsis

% Constellation parameters
numPlanesLEO = 20; % Number of orbital planes
satellitesPerPlane = 10; % Satellites per orbital plane
totalLEOSatellites = numPlanesLEO * satellitesPerPlane; % Total satellites
planeSeparation = 360 / numPlanesLEO; % Plane separation in degrees
satelliteSeparation = 360 / satellitesPerPlane; % Satellite separation within the plane

% Create satellites in stepped constellation
for plane = 0:numPlanesLEO-1
    raanLEO = plane * planeSeparation; % RAAN for each plane
    for sat = 0:satellitesPerPlane-1
        trueAnomalyLEO = sat * satelliteSeparation; % Offset within the plane
        leoSat = satellite(sc, semiMajorAxisLEO, eccentricityLEO, ...
            inclinationLEO, raanLEO, argumentOfPeriapsisLEO, trueAnomalyLEO, ...
            "Name", sprintf("LEO Sat %d-%d", plane+1, sat+1));
    end
end

% --- GROUND STATIONS ---
% Uplink stations (Santo Domingo, Santiago, La Romana, Puerto Plata,
% San Juan, Barahona, Higüey, San Francisco de Macorís) and download link
% points in rural areas (border region, Bahoruco, Monte Plata, Constanza).
% Coordinates are read from data/estaciones.csv.
uplinks = cargar_estaciones(sc, "uplink");
downlinks = cargar_estaciones(sc, "downlink");

% --- VISUALIZATION ---
% Visualize the scenario with satellites and stations
satelliteScenarioViewer(sc);

% Display satellite information
disp("Satellites created:");
disp(sc.Satellites);

% Display ground station information
disp("Ground stations:");
disp(sc.GroundStations);

