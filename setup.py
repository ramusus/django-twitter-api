import re

from setuptools import find_packages, setup

setup(
    name='django-twitter-api',
    version=__import__('twitter_api').__version__,
    description='Django implementation for Twitter API',
    long_description=open('README.md').read(),
    author='ramusus',
    author_email='ramusus@gmail.com',
    url='https://github.com/ramusus/django-twitter-api',
    download_url='http://pypi.python.org/pypi/django-twitter-api',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,  # because we're including media that Django needs
    install_requires=[
        'django',
        'django-annoying',
        'django-picklefield',
        'django-m2m-history',
        'django-oauth-tokens>=0.4.10',
        'django-m2m-history>=0.2.0',
        'tweepy',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
