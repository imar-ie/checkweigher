from setuptools import setup, find_packages

setup(
  name="yamatocheckweigher",

  version="0.1.13",

  author="Keith Phelan",

  packages=find_packages(exclude=['dmp']),

  #long_description=read('README.md')

  package_data={'checkweigher': ['configs/*.yaml']},

)
