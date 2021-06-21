import pathlib
from setuptools import setup, find_packages

# read the contents of README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

HERE = pathlib.Path(__file__).parent



setup(
    name='gitlab2prov',
    version='0.5',
    author='Claas de Boer',
    author_email='claas.deboer@dlr.de',
    maintainer='Andreas Schreiber',
    maintainer_email='andreas.schreiber@dlr.de',
    description='Extract provenance information (W3C PROV) from GitLab projects.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords=[
        'prov',
        'gitlab',
        'provenance',
        'prov generation',
        'software analytics',
        'w3c prov'
    ],
    url='https://github.com/DLR-SC/gitlab2prov',
    packages=find_packages(),
    install_requires=[
        'prov==2.0.0',
        'pydot',
        'aiohttp',
        'yarl',
    ],
    entry_points={'console_scripts': ['gitlab2prov=gitlab2prov.cli:main']},
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Software Development :: Version Control :: Git',
        ],
    include_package_data=True,
)
