from setuptools import setup, find_packages

setup(
  name="yamatocheckweigher",

  version="0.1.19",

  author="Keith Phelan",

  packages=find_packages(),

  package_data={'yamatocheckweigher': ['configs/*.yaml']},

)
