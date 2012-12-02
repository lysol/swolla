try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(name='swolla',
  version='0.1',
  description='swolla',
  author='Derek Arnold',
  author_email='derek@swolla.derekarnold.net',
  url='http://swolla.derekarnold.net',
  packages=['swolla'],
  zip_safe=False,
  install_requires=[
      'Flask',
      'psycopg2',
      'candle',
      'twilio',
      'dwolla'
      ],
  include_package_data=True
)
