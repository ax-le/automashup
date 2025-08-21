import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="automashup",
    version="0.1.0",
    description="Package for automashup.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ax-le/automashup",
    packages=setuptools.find_packages(),
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Programming Language :: Python :: 3.10"
    ],
    license='BSD',
    install_requires=[
        'allin1 == 1.1.0',
        'barfi',
        'matplotlib',
        'demucs == 4.0.1',
        'essentia == 2.1b6.dev1110',
        'librosa == 0.10.1',
        'numpy == 1.26.4',
        'pandas',
        'soundfile == 0.12.1',
        'streamlit',
        'torch == 2.2.2',
        'torchaudio == 2.2.2',
        'pydub',
        'pyrubberband',
        'pyloudnorm',
        'madmom @ git+https://github.com/CPJKU/madmom',
    ],
    python_requires='>=3.10',
)