from setuptools import setup

setup(
    name='memfog',
    version='1.6.3',
    author='Evan Henri',
    packages=['src',],
    license='MIT',
    long_description=open('README.md').read(),
    keywords='extendable memory recall utility',
    url='https://github.com/evanhenri/memfog',
    install_requires=[
        'docopt >= 0.6.2',
        'fuzzywuzzy >= 0.8.1',
        'SQLAlchemy >= 1.0.9',
        'urwid >= 1.3.1',
    ],
    entry_points={
        'console_scripts': [
            'memfog = src.__main__:main'
        ]
    }
)
