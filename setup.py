from setuptools import setup, find_packages

setup(
    name = 'Cottage Labs Catalogue',
    version = '0.0.1',
    packages = find_packages(),
    install_requires = [
        "Flask==0.10.1",
        "Flask-Login==0.2.7",
        "requests==2.1.0",
        "gunicorn",
        "newrelic"
    ],
    url = 'http://cottagelabs.com/',
    author = 'Cottage Labs',
    author_email = 'us@cottagelabs.com',
    description = 'Provision of a web API wrapper around cottagelabs catalogue',
    license = 'Copyheart',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: Copyheart',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
