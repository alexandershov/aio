from setuptools import find_packages
from setuptools import setup

setup(
    name='aio',
    version='0.1.0',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    entry_points={
        'console_scripts': [
            'coro_server = aio.coro_server:main',
            'callbacks_server = aio.callbacks_server:main',
        ]
    },
    tests_require=['pytest'],
)
