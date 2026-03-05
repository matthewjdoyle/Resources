% Generate test dataset with step changes
X = [randn(1, 100), randn(1, 30) + 5, randn(1, 70)];
n = 1:length(X);

% Set the window size and threshold for step change detection
windowSize = 10;
threshold = 0.5;

% Detect the location of step changes
stepChangeIndices = detectStepChange(X, windowSize, threshold);

% Plot the data and rolling average
rollingAvg = movmean(X, windowSize);
plot(n, X, n, rollingAvg)

% Display the detected step change indices
disp(stepChangeIndices);