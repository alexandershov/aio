from setuptools import find_packages
from setuptools import setup

setup(
    name='aio',
    version='0.1.0',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    entry_points={
        'console_scripts': [
            'callback_server = aio.callback_server:main',
        ]
    }
)
