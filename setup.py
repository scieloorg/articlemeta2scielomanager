#!/usr/bin/env python
from setuptools import setup, find_packages

install_requires = [
    'thriftpy==0.3.1',
    'xylose',
    'packtools',
    'lxml>=3.5.0'
]

tests_require = []

setup(
    name="processing",
    version="0.1",
    description="Aplicativo para envio de XML's SciELO PS do Article Meta para o SciELO Manager",
    author="SciELO",
    author_email="scielo-dev@googlegroups.com",
    maintainer="Fabio Batalha",
    maintainer_email="fabio.batalha@scielo.org",
    url="http://github.com/scieloorg/processing",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 2.7",
    ],
    dependency_links=[
        "git+https://git@github.com/scieloorg/xylose.git@v0.34#egg=xylose",
    ],
    tests_require=tests_require,
    test_suite='tests',
    install_requires=install_requires,
    entry_points="""
    [console_scripts]
    am2sm=articlemeta2scielomanager.am2sm:main
    """
)
