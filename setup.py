from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='msdparser',
      version='0.1.3',
      description='Simple MSD parser (rhythm game format)',
      long_description=long_description,
      long_description_content_type='text/markdown',
      keywords='stepmania simfile sm ssc dwi',
      url='http://github.com/garcia/msdparser',
      author='Ash Garcia',
      author_email='msdparser@garcia.sh',
      license='MIT',
      packages=['msdparser'],
      python_requires='>=3.6',
      zip_safe=True)