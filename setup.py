from pathlib import Path
from typing import Any

from setuptools import setup


def load_module_dict(filename: str) -> dict:
    import importlib.util as ilu
    filename = Path(__file__).parent / filename
    spec = ilu.spec_from_file_location('', filename)
    module = ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.__dict__


name = "chkpkg"
constants = load_module_dict(f'{name}/_constants.py')

setup(
    name=name,
    version=constants['__version__'],
    author=constants['__author__'],
    author_email=constants['__author_email__'],
    url=constants['__url__'],

    python_requires='>=3.6',
    install_requires=[],
    packages=[name],

    description=constants['__summary__'],

    keywords=constants['__keywords__'],

    long_description=(Path(__file__).parent / 'README.md')
        .read_text(encoding='utf-8'),  # need encoding for Windows
    long_description_content_type='text/markdown',

    license=constants['__license__'],

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
