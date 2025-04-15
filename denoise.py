from scipy.signal import butter, filtfilt

def bandpass_filter(data, lowcut=100.0, highcut=3800.0, fs=8000, order=4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, data)

def trim_silence(pcm_data, threshold=500, chunk_size=160):
    start = 0
    end = len(pcm_data)

    # Find start
    for i in range(0, len(pcm_data), chunk_size):
        if np.abs(pcm_data[i:i+chunk_size]).mean() > threshold:
            start = i
            break

    # Find end
    for i in range(len(pcm_data) - chunk_size, 0, -chunk_size):
        if np.abs(pcm_data[i:i+chunk_size]).mean() > threshold:
            end = i + chunk_size
            break

    return pcm_data[start:end]
