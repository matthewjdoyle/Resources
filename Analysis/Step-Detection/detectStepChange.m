function stepChangeIndices = detectStepChange(X, windowSize, threshold)
% DETECTSTEPCHANGE Detects the location of a step change in the rolling average of data.
%   STEPCHANGEINDICES = DETECTSTEPCHANGE(X, WINDOWSIZE, THRESHOLD) detects
%   the location (or indices) of a step change in the rolling average of
%   the input data X. The rolling average is computed using a window of
%   size WINDOWSIZE. The threshold parameter determines the sensitivity
%   for detecting a step change.

% Compute the rolling average
rollingAvg = movmean(X, windowSize);

% Calculate the differences between consecutive rolling averages
diffs = diff(rollingAvg);

% Find the indices where the differences exceed the threshold
stepChangeIndices = find(abs(diffs) > threshold);

end

% Generate test dataset with step changes
% X = [randn(1, 100), randn(1, 30) + 5, randn(1, 70)];

% Set the window size and threshold for step change detection
% windowSize = 10;
% threshold = 3;
% 
% Detect the location of step changes
% stepChangeIndices = detectStepChange(X, windowSize, threshold);

% Display the detected step change indices
% disp(stepChangeIndices);