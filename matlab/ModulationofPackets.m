% Configurable parameters
n_packets = 10;            % Number of packets to send
avg_latency = 0.1;         % Average latency between packets (in seconds)
latency_threshold = 0.15;  % Above this latency packets are fragmented (in seconds)

% Simulation Parameters
fs = 10000;        % Sampling frequency (in Hz)
f_carrier_upload = 2000;  % Carrier frequency for the upload link (in Hz)
f_carrier_download = 1000; % Carrier frequency for the download link (in Hz)
f_message = 50;    % Message signal frequency (in Hz)
t = 0:1/fs:0.2;    % Simulation time for a packet (0.2 seconds)

% Message signal (representing a data packet)
message_signal = sin(2*pi*f_message*t);

% Amplitude Modulation (AM) for each link
am_signal_upload = (1 + 0.5 * message_signal) .* cos(2*pi*f_carrier_upload*t);
am_signal_download = (1 + 0.5 * message_signal) .* cos(2*pi*f_carrier_download*t);

% Plot the modulated signal for both links
figure;

% Upload link
subplot(3, 1, 1);
plot(t, am_signal_upload, 'b');
title('Upload Link: AM Modulated Signal');
xlabel('Time (s)');
ylabel('Amplitude');
grid on;

% Download link
subplot(3, 1, 2);
plot(t, am_signal_download, 'g');
title('Download Link: AM Modulated Signal');
xlabel('Time (s)');
ylabel('Amplitude');
grid on;

% Simulate the transmission of 10 packets with latency
subplot(3, 1, 3);
hold on;
title('Packet Transmission');
xlabel('Time (s)');
ylabel('Amplitude');
grid on;

% With high latency each packet is split into fragments
n_fragments = max(1, ceil(avg_latency / latency_threshold));
fragment_edges = round(linspace(1, numel(t), n_fragments + 1));
fprintf("Sending %d packets with %.0f ms latency (%d fragment(s) per packet)\n", ...
    n_packets, avg_latency * 1000, n_fragments);

for i = 1:n_packets
    for f = 1:n_fragments
        idx = fragment_edges(f):fragment_edges(f + 1);
        gap = (f - 1) * avg_latency / n_fragments;  % extra delay between fragments

        % Send fragment from Upload Link to satellite
        plot(t(idx) + (i-1)*avg_latency + gap, am_signal_upload(idx), 'r');
        pause(0.2 / n_fragments);  % Simulate upload transmission latency

        % Send fragment from satellite to Download Link
        plot(t(idx) + (i-1)*avg_latency + gap + 0.1, am_signal_download(idx), 'k');
        pause(0.2 / n_fragments);  % Simulate download reception latency
    end
end

hold off;
