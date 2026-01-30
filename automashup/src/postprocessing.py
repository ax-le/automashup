import soundfile as sf
import os
import pyloudnorm as pyln

def save_song(audio, sr, save_folder_path, mashup_name, add_name=""):
    os.makedirs(save_folder_path, exist_ok=True)
    final_mashup_path = f"{save_folder_path}/mashup_{mashup_name}_{add_name}.wav"
    sf.write(final_mashup_path, audio, sr)
    print(f"Saved mashup to {final_mashup_path}")
    return final_mashup_path


def normalize_lufs(audio, sr, target_lufs=-14.0, verbose = True):
    # Apply LUFS normalization to the mashup
    meter = pyln.Meter(sr)  # Create a BS.1770 loudness meter
    current_lufs = meter.integrated_loudness(audio)  # Measure the loudness
    if verbose:
        print(f"Mashup loudness (before normalization): {current_lufs} LUFS")

    # Normalize the mashup to the target loudness (-14 LUFS by deafult)
    audio = pyln.normalize.loudness(audio, current_lufs, target_lufs)
    if verbose:
        print(f"Mashup normalized to {target_lufs} LUFS")
    return audio