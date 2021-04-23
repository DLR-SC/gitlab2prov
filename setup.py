import pathlib
from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent

setup(
    name='gitlab2prov',
    version='0.4.1',
    author='Claas de Boer',
    author_email='claas.deboer@dlr.de',
    maintainer='Andreas Schreiber',
    maintainer_email='andreas.schreiber@dlr.de',
    description='Extract provenance information (W3C PROV) from GitLab projects.',
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
