# MATLAB Rolling-Average Step Detector

Detect abrupt step changes in noisy 1D data using a rolling average and threshold.

## Why This Approach?

Step changes — abrupt shifts in a signal's baseline level — are a common feature in experimental and time-series data. A natural way to detect them is to look for spikes in the signal's derivative, since a step produces a large instantaneous rate of change while stationary regions produce near-zero derivatives. By thresholding the derivative magnitude, we can isolate the moments where transitions occur without needing to know the signal's shape or distribution in advance. This makes the method simple, general-purpose, and easy to tune with just two parameters: window size and threshold.

## How It Works

1. Smooth the input signal with a rolling average (`movmean`)
2. Differentiate the smoothed signal (`diff`)
3. Return indices where the absolute change exceeds a threshold

### Why smooth before differentiating?

Differentiating raw data (`diff(X)`) amplifies noise, making it difficult to distinguish real step changes from random fluctuations without an impractically high threshold. By smoothing first, the rolling average suppresses noise so that the derivative reflects genuine shifts in the signal level. The tradeoff is that detected steps are spread across a cluster of ~`windowSize` indices rather than a single point, identifying the *region* of each transition rather than a precise location.

## Usage

```matlab
X = [randn(1,100), randn(1,30) + 5, randn(1,70)];
indices = detectStepChange(X, 10, 0.5);
```

### Parameters

| Parameter | Description |
|---|---|
| `X` | 1D input signal |
| `windowSize` | Number of samples for the rolling average |
| `threshold` | Minimum derivative magnitude to flag as a step change |

### Returns

A vector of indices where step changes were detected.

## Files

- **`detectStepChange.m`** — Core detection function.
- **`testStepChange.m`** — Demo script that generates synthetic data with a known step, runs detection, and plots the result.
