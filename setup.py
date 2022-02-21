from setuptools import setup, find_packages

setup(
  name="yamatocheckweigher",

  version="0.1.18",

  author="Keith Phelan",

  packages=find_packages(),

  package_data={'checkweigher': ['configs/*.yaml']},

)
