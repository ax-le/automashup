import torch.nn.functional as F
import os
import torch
import numpy as np
import librosa
from itertools import product  # Pour générer toutes les paires possibles
from cocola.contrastive_model import constants
from cocola.contrastive_model.contrastive_model import CoCola
from cocola.feature_extraction.feature_extraction import CoColaFeatureExtractor
import sys
sys.path.append("./cocola")
import torchaudio
import torchaudio.transforms as T

# 🖥️ Détection GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🔹 Using device: {device}")

# 📂 Dossier contenant les fichiers `.pt`
features_folder = "./features_cocola"

# 🔄 Charger le modèle pré-entraîné Cocola sur GPU
model = CoCola.load_from_checkpoint(
    "./cocola/checkpoint.ckpt", 
    input_type=constants.ModelInputType.DOUBLE_CHANNEL_HARMONIC_PERCUSSIVE
).to(device)
model.eval()

# 📌 Fonction pour charger et padder les features
def load_features(file_path):
    features = torch.load(file_path, map_location=device)
    if len(features.shape) == 2:
        features = features.unsqueeze(0)  # Ensure shape [1, C, T]
    return features

# 📂 Récupérer les fichiers `.pt` pour vocals et instrumentals
vocals_features = {k: v.to(device) for k, v in torch.load(os.path.join(features_folder, "vocals_features.pt")).items()}
instrumentals_features = {k: v.to(device) for k, v in torch.load(os.path.join(features_folder, "instrumentals_features.pt")).items()}


def truncate_or_pad_features(features_dict, max_length=None):
    """Truncate or pad features to a max reasonable length"""
    lengths = [tensor.shape[2] for tensor in features_dict.values()]
    
    if max_length is None:
        max_length = int(np.median(lengths))  # Use median to avoid extreme values
    
    for key in features_dict:
        tensor = features_dict[key]
        current_length = tensor.shape[2]
        
        if current_length > max_length:
            # Truncate
            features_dict[key] = tensor[:, :, :max_length].to(device)
        elif current_length < max_length:
            # Pad
            pad_amount = max_length - current_length
            features_dict[key] = F.pad(tensor, (0, pad_amount), "constant", 0).to(device)
        else:
            # Ensure it's on the correct device even if no modification
            features_dict[key] = tensor.to(device)
    
    return features_dict

# Appliquer la normalisation
vocals_features = truncate_or_pad_features(vocals_features)
instrumentals_features = truncate_or_pad_features(instrumentals_features)


# Diviser les caractéristiques en segments plus petits
def segment_features(feature_tensor, num_segments=4):
    """Découpe un tenseur de caractéristiques en segments plus petits"""
    time_dim = feature_tensor.shape[2]
    segment_length = time_dim // num_segments
    segments = []
    
    for i in range(num_segments):
        start_idx = i * segment_length
        end_idx = start_idx + segment_length if i < num_segments-1 else time_dim
        segment = feature_tensor[:, :, start_idx:end_idx]
        segments.append(segment)
    
    return segments

# Calculer les scores par segments
def compute_segmented_score(vocals_feature, instr_feature, num_segments=4):
    vocals_segments = segment_features(vocals_feature, num_segments)
    instr_segments = segment_features(instr_feature, num_segments)
    
    segment_scores = []
    
    for v_seg, i_seg in zip(vocals_segments, instr_segments):
        # Calculer le score pour ce segment
        score = model.score(v_seg, i_seg).item()
        segment_scores.append(score)
        # Libérer la mémoire GPU
        torch.cuda.empty_cache()
    
    # Retourner la moyenne des scores des segments
    return sum(segment_scores) / len(segment_scores)

# Utiliser cette fonction pour chaque paire
cocola_scores = {}
all_pairs = list(product(vocals_features.keys(), instrumentals_features.keys()))
total_pairs = len(all_pairs)

for idx, (vocals_music, instr_music) in enumerate(all_pairs):
    features_vocals = vocals_features[vocals_music]
    features_instr = instrumentals_features[instr_music]

    # Calculer le score en utilisant des segments
    cocola_score = compute_segmented_score(features_vocals, features_instr, num_segments=4)
    
    cocola_scores[(vocals_music, instr_music)] = cocola_score
    print(f"✅ {idx+1}/{total_pairs}: {vocals_music} (vocals) - {instr_music} (instrumental) : {cocola_score:.4f}")
    
    # Libérer la mémoire
    torch.cuda.empty_cache()
    
# 🔹 Display final results
print("\n🔹 Cocola Scores Summary:")
for (vocals_music, instr_music), score in cocola_scores.items():
    print(f"{vocals_music} (vocals) - {instr_music} (instrumental) : {score:.4f}")


# Sauvegarde des résultats dans un fichier CSV
with open("cocola_scores.csv", "w") as f:
    f.write("vocals,instrumental,score\n")
    for (vocals_music, instr_music), score in cocola_scores.items():
        f.write(f"{vocals_music},{instr_music},{score}\n")
print("\n📂 Fichier `cocola_scores.csv` créé avec succès !")
