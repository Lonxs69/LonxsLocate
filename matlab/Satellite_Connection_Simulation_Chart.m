% Definition of geographic coordinates for Santo Domingo (latitude and longitude)
lat_santodomingo = 18.4861;   % Latitude of Santo Domingo (in degrees)
lon_santodomingo = -69.9312;  % Longitude of Santo Domingo (in degrees)

% Geographic coordinates for Pedernales (download)
lat_pedernales = 18.0384;   % Latitude of Pedernales (in degrees)
lon_pedernales = -71.7440;  % Longitude of Pedernales (in degrees)

% Parameters of the LEO satellite
altitude_satellite = 600;  % Altitude in km
lat_satellite = 18.7;      % Latitude of the satellite over the Dominican Republic (approximate)
lon_satellite = -70.5;    % Longitude of the satellite over the Dominican Republic (approximate)

% Earth's radius (in km)
radius_earth = 6371;

% Convert geographic coordinates to radians
lat_santodomingo_rad = deg2rad(lat_santodomingo);
lon_santodomingo_rad = deg2rad(lon_santodomingo);
lat_pedernales_rad = deg2rad(lat_pedernales);
lon_pedernales_rad = deg2rad(lon_pedernales);
lat_satellite_rad = deg2rad(lat_satellite);
lon_satellite_rad = deg2rad(lon_satellite);

% Cartesian coordinates
% Santo Domingo
x_santodomingo = radius_earth * cos(lat_santodomingo_rad) * cos(lon_santodomingo_rad);
y_santodomingo = radius_earth * cos(lat_santodomingo_rad) * sin(lon_santodomingo_rad);
z_santodomingo = radius_earth * sin(lat_santodomingo_rad);

% Pedernales
x_pedernales = radius_earth * cos(lat_pedernales_rad) * cos(lon_pedernales_rad);
y_pedernales = radius_earth * cos(lat_pedernales_rad) * sin(lon_pedernales_rad);
z_pedernales = radius_earth * sin(lat_pedernales_rad);

% Satellite
x_satellite = (radius_earth + altitude_satellite) * cos(lat_satellite_rad) * cos(lon_satellite_rad);
y_satellite = (radius_earth + altitude_satellite) * cos(lat_satellite_rad) * sin(lon_satellite_rad);
z_satellite = (radius_earth + altitude_satellite) * sin(lat_satellite_rad);

% Plot Earth with satellite's orbit
figure;
hold on;

% Create Earth sphere with no color, just the border
[earth_x, earth_y, earth_z] = sphere(100);
surf(earth_x * radius_earth, earth_y * radius_earth, earth_z * radius_earth, 'FaceColor', 'none', 'EdgeColor', [0.5 0.5 0.5]);

% Plot satellite's orbit as a dashed line
theta = linspace(0, 2*pi, 200);  % Angle for the orbit
x_orbit = (radius_earth + altitude_satellite) * cos(theta);
y_orbit = (radius_earth + altitude_satellite) * sin(theta);
z_orbit = zeros(size(theta));  % Assuming orbit in the equatorial plane
plot3(x_orbit, y_orbit, z_orbit, 'k--', 'LineWidth', 1.5);

% Plot communication links (upload and download)
plot3([x_santodomingo, x_satellite], [y_santodomingo, y_satellite], [z_santodomingo, z_satellite], 'r-', 'LineWidth', 2); % Upload
plot3([x_satellite, x_pedernales], [y_satellite, y_pedernales], [z_satellite, z_pedernales], 'b-', 'LineWidth', 2); % Download

% Plot positions
plot3(x_santodomingo, y_santodomingo, z_santodomingo, 'go', 'MarkerFaceColor', 'g');  % Santo Domingo (upload link)
plot3(x_pedernales, y_pedernales, z_pedernales, 'mo', 'MarkerFaceColor', 'm');  % Pedernales (download link)
plot3(x_satellite, y_satellite, z_satellite, 'ko', 'MarkerFaceColor', 'k');  % Satellite

% Labels and configuration
title('Satellite in Orbit over the Dominican Republic with Communication Links');
xlabel('X (km)');
ylabel('Y (km)');
zlabel('Z (km)');
legend('Earth (Silhouette)', 'Satellite Orbit', 'Upload Link', 'Download Link', ...
       'Santo Domingo (Base Station)', 'Pedernales (Download Station)', 'Satellite');
grid on;
axis equal;
hold off;
