# -*- coding: utf-8 -*-
from setuptools import find_packages, setup


setup(
    name="widgetastic.core",
    use_scm_version=True,
    author="Milan Falesnik",
    author_email="mfalesni@redhat.com",
    description="Library designed for representing complex UIs for testing.",
    license="Apache license",
    url="https://github.com/RedHatQE/widgetastic.core",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'cached_property',
        'selenium',
        'selenium-smart-locator',
        'wait_for',
    ],
    setup_requires=[
        'setuptools_scm',
    ],
    # TODO: Classifiers
    namespace_packages=['widgetastic']
)
