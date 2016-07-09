try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

VERSION = '0.1.0.dev0'

LONG_DESCRIPTION = None
try:
    LONG_DESCRIPTION = open('README.rst').read()
except Exception:
    pass


CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: Implementation :: CPython"
]


setup(
    name='mongomodels',
    version=VERSION,
    author='Luke Lovett/Elizabeth Bennett',
    author_email='liz@{nospam}bennettworld.org',
    license='Apache License, Version 2.0',
    include_package_data=True,
    description='MSB is My Sweet Blog.',
    long_description=LONG_DESCRIPTION,
    packages=find_packages(exclude=['test', 'test.*']),
    platforms=['any'],
    classifiers=CLASSIFIERS,
    test_suite='test',
    install_requires=['mongomodels>=0.1.0.dev0', 'Flask>=0.11.1'],
    extras_require={'images': 'Pillow'}
)
