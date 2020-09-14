from setuptools import setup

from msdparser import __version__ as version


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='msdparser',
    version=version,
    description='Simple MSD parser (rhythm game format)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Ash Garcia',
    author_email='python-msdparser@garcia.sh',
    url='http://github.com/garcia/msdparser',
    packages=['msdparser'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Topic :: Games/Entertainment',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Typing :: Typed',
    ],
    license='MIT',
    keywords='stepmania simfile sm ssc dwi',
    python_requires='>=3.6',
    zip_safe=False,
    command_options={
        'build_sphinx': {
            'version': ('setup.py', version),
        },
    },
)