from pathlib import Path
from setuptools import setup


def load_module_dict(filename: str) -> dict:
    import importlib.util as ilu
    filename = Path(__file__).parent / filename
    spec = ilu.spec_from_file_location('', filename)
    module = ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.__dict__


name = "chkpkg"

setup(
    name=name,
    version=load_module_dict(f'{name}/_constants.py')['__version__'],
    author="Artёm IG",
    author_email="ortemeo@gmail.com",
    url='https://github.com/rtmigo/chkpkg_py#readme',

    python_requires='>=3.6',
    install_requires=[],
    packages=[name],

    description="Checks Python packages intended to be published on PyPi",

    keywords="wheel package distribution wheel whl testing".split(),

    long_description=(Path(__file__).parent / 'README.md')
        .read_text(encoding='utf-8'),  # need encoding for Windows
    long_description_content_type='text/markdown',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
    ],
)
