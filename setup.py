#!/usr/bin/env python
from setuptools import setup, find_packages

install_requires = [
    'thriftpy==0.3.1',
    'xylose',
    'packtools',
    'lxml==3.4.4'
]

tests_require = []

setup(
    name="articlemeta2scielomanager",
    version="0.1",
    description="Aplicativo para envio de XML's SciELO PS do Article Meta para o SciELO Manager",
    author="SciELO",
    author_email="scielo-dev@googlegroups.com",
    maintainer="Fabio Batalha",
    maintainer_email="fabio.batalha@scielo.org",
    url="http://github.com/scieloorg/articlemeta2scielomanager",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 2.7",
    ],
    dependency_links=[
        "git+https://git@github.com/scieloorg/xylose.git@v0.44#egg=xylose",
    ],
    setup_requires=["nose>=1.0", "coverage"],
    tests_require=tests_require,
    test_suite="tests",
    install_requires=install_requires,
    entry_points="""
    [console_scripts]
    am2sm=exporter:main
    aid2am=load_aid:main
    """
)
