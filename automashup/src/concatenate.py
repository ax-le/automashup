import numpy as np

def concatenate_sections(list_of_audios): # Might be complicated if sections are not bar-aligned.
    """
    Concatenate a list of audio arrays into a single audio array.
    
    Args:
        list_of_audios: List of audio arrays
    
    Returns:
        np.ndarray: Concatenated audio array
    """
    if not list_of_audios:
        raise ValueError("Empty list of audios provided")
    
    concatenated = np.concatenate(list_of_audios)
    return concatenated